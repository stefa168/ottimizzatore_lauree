from __future__ import annotations

import json
import pathlib
import shutil
from typing import Final

import structlog
from aio_pika import Message, DeliveryMode
from litestar import Controller, get, patch, delete
from litestar.di import Provide
from litestar.dto import DTOData
from litestar.exceptions import HTTPException
import litestar.status_codes as http_statuses

from v2.db.models import OptimizationConfiguration
from v2.domain.grad_sessions import urls
from v2.domain.grad_sessions.deps import (
    SessionEntryRepository,
    OptimizationConfigurationRepository,
    GradSessionRepository
)
from v2.domain.grad_sessions.schemas import OptConfDTO, OptConfPatchDTO, OptConfListDTO, OptConfCompleteDTO
from v2.domain.grad_sessions.services import check_gs_exists_raise, get_opt_conf_raise
from v2.opt_manager import RabbitMessaging, OPTIMIZATION_CHANNEL_NAME

logger = structlog.stdlib.get_logger(__name__)

# Path to the directories that hold the datfiles and solutions produced.
# Inside this directory there is a directory with this structure:
# temp
# |- [problem_id] - [config_id] --- cfg.dat
# |_ ...                         |_ model.lp
#                                |_ val.xls
OPT_TMP_DIR: Final = ".temp/"


class OptimizationConfigurationController(Controller):
    """Optimization Configuration Controller"""

    tags = ["Graduation Sessions", "Optimization", "Configuration"]
    dependencies = {
        "grad_session_repository": Provide(GradSessionRepository.provide),
        "session_entry_repository": Provide(SessionEntryRepository.provide),
        "opt_conf_repo": Provide(OptimizationConfigurationRepository.provide)
    }

    @get(urls.GRAD_SESSION_OPT_CONF_NEW, return_dto=OptConfDTO)
    async def new_configuration(self, sid: int,
                                grad_session_repository: GradSessionRepository,
                                opt_conf_repo: OptimizationConfigurationRepository) -> OptimizationConfiguration:
        await check_gs_exists_raise(grad_session_repository, sid)

        conf_count = await opt_conf_repo.count(OptimizationConfiguration.session_id == sid)

        conf = await opt_conf_repo.add(OptimizationConfiguration(session_id=sid))
        conf.title += f" {conf_count + 1}"

        return conf

    @get(urls.GRAD_SESSION_OPT_CONF_LIST, return_dto=OptConfListDTO)
    async def configuration_list(self, sid: int,
                                 grad_session_repository: GradSessionRepository,
                                 opt_conf_repo: OptimizationConfigurationRepository) -> list[OptimizationConfiguration]:
        await check_gs_exists_raise(grad_session_repository, sid)
        return await opt_conf_repo.list(OptimizationConfiguration.session_id == sid)

    @patch(urls.GRAD_SESSION_OPT_CONF_UPDATE, dto=OptConfPatchDTO, return_dto=OptConfDTO)
    async def update_configuration(self, sid: int, cid: int,
                                   data: DTOData[OptimizationConfiguration],
                                   opt_conf_repo: OptimizationConfigurationRepository
                                   ) -> OptimizationConfiguration:
        config = await get_opt_conf_raise(cid, sid, opt_conf_repo)
        return data.update_instance(config)

    @delete(urls.GRAD_SESSION_OPT_CONF_UPDATE, status_code=http_statuses.HTTP_200_OK)
    async def update_configuration(self, sid: int, cid: int,
                                   opt_conf_repo: OptimizationConfigurationRepository
                                   ) -> None:
        await get_opt_conf_raise(cid, sid, opt_conf_repo)
        await opt_conf_repo.delete(cid)

    @get(urls.GRAD_SESSION_OPT_CONF_GET_COMPLETE)
    async def get_complete_configuration(self, sid: int, cid: int,
                                         grad_session_repository: GradSessionRepository,
                                         opt_conf_repo: OptimizationConfigurationRepository
                                         ) -> OptConfCompleteDTO:
        await check_gs_exists_raise(grad_session_repository, sid)
        config = await get_opt_conf_raise(cid, sid, opt_conf_repo)
        return OptConfCompleteDTO.model_validate(config)

    @get(urls.GRAD_SESSION_OPT_CONF_SOLVE, status_code=http_statuses.HTTP_202_ACCEPTED)
    async def solve_configuration(self, session_id: int, config_id: int,
                                  pika: RabbitMessaging,
                                  grad_session_repository: GradSessionRepository,
                                  opt_conf_repo: OptimizationConfigurationRepository) -> None:
        logger.info(f"Received request to solve commission {session_id} with configuration {config_id}")

        # executor.queue.append("1345")
        # logger.info(executor.queue.popleft())
        # return

        await check_gs_exists_raise(grad_session_repository, session_id)
        config = await get_opt_conf_raise(config_id, session_id, opt_conf_repo)

        # First we check if the configuration has already been solved
        if len(config.commissions) > 0:
            logger.error(f"Configuration with ID {config_id} already solved")
            raise HTTPException(
                detail="Configuration already solved",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        # Then we check if the configuration is already running. If we're here, we're sure that we haven't saved a
        # solution yet.
        # todo we should return another kind of error if the lock is set but there is no future currently running
        if config.run_lock:
            logger.error(f"Configuration with ID {config_id} is already being solved")
            raise HTTPException(
                detail="Configuration with ID {config_id} is already being solved",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        logger.debug(f"Locking the configuration {config_id}")
        # todo enable after testing
        # config.run_lock = True
        # await opt_conf_repo.update(config)

        logger.debug(f"Setting up the optimization for session {session_id} and configuration {config_id}")
        base_path = pathlib.Path(OPT_TMP_DIR)
        cc_path = base_path / str(session_id) / str(config_id)

        cc_path.mkdir(parents=True, exist_ok=True)

        try:
            config.create_dat_file(cc_path)

            with (cc_path / "val.xls").open('wb') as f:
                f.write(config.session.export_xls())
        except Exception as e:
            logger.error(f"Error during optimization files creation for session {session_id}, config {config_id}", e)
            if cc_path.exists():
                shutil.rmtree(cc_path)
                logger.debug(f"Deleted directory {cc_path} due to export error")

            raise

        await pika.channel.default_exchange.publish(
            Message(
                b"test",
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key="optimization"
        )

        # tasks = BackgroundTasks([BackgroundTask(solver_wrapper, config, cc_path)])

        # return Response(
        #     background=tasks,
        #     status_code=http_statuses.HTTP_202_ACCEPTED,
        #     content=None
        # )
