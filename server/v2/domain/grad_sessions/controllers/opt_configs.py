from __future__ import annotations

import re
import shutil
from urllib.parse import quote

import structlog
from litestar import Controller, Response, get, patch, delete, post
from litestar.di import Provide
from litestar.dto import DTOData
from litestar.exceptions import HTTPException
import litestar.status_codes as http_statuses
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from v2.db.models import SolutionCommission
from v2.db.models import OptimizationConfiguration
from v2.domain.grad_sessions import urls
from v2.domain.grad_sessions.deps import (
    SessionEntryRepository,
    OptimizationConfigurationRepository,
    GradSessionRepository
)
from v2.domain.grad_sessions.schemas import OptConfDTO, OptConfPatchDTO, OptConfListDTO, OptConfCompleteDTO, \
    CloneOptConfDTO
from v2.domain.grad_sessions.services import check_gs_exists_raise, get_opt_conf_raise
from v2.domain.grad_sessions.solution_export import XLSX_MEDIA_TYPE, build_solution_xlsx
from v2.utils import job_queue

logger = structlog.stdlib.get_logger(__name__)


def raise_if_frozen(config: OptimizationConfiguration) -> None:
    if config.frozen:
        raise HTTPException(
            detail="The configuration is frozen: unfreeze it before changing or deleting it",
            status_code=http_statuses.HTTP_409_CONFLICT
        )


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

    @post(urls.GRAD_SESSION_OPT_CONF_NEW, dto=CloneOptConfDTO, return_dto=OptConfDTO)
    async def clone_configuration(self, sid: int,
                                  data: DTOData[OptimizationConfiguration],
                                  grad_session_repository: GradSessionRepository,
                                  opt_conf_repo: OptimizationConfigurationRepository) -> OptimizationConfiguration:
        await check_gs_exists_raise(grad_session_repository, sid)
        new_instance = data.create_instance(run_lock=False, online=True)
        new_instance.title += " (Copia)"

        return await opt_conf_repo.add(new_instance)

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
        raise_if_frozen(config)
        return data.update_instance(config)

    @delete(urls.GRAD_SESSION_OPT_CONF_UPDATE, status_code=http_statuses.HTTP_200_OK)
    async def delete_configuration(self, sid: int, cid: int,
                                   opt_conf_repo: OptimizationConfigurationRepository
                                   ) -> None:
        config = await get_opt_conf_raise(cid, sid, opt_conf_repo)
        raise_if_frozen(config)
        await opt_conf_repo.delete(cid)

    @post(urls.GRAD_SESSION_OPT_CONF_FREEZE, return_dto=OptConfDTO, status_code=http_statuses.HTTP_200_OK)
    async def freeze_configuration(self, sid: int, cid: int,
                                   opt_conf_repo: OptimizationConfigurationRepository
                                   ) -> OptimizationConfiguration:
        """Marks the solution of the configuration as final: the configuration can't be changed or deleted."""
        config = await get_opt_conf_raise(cid, sid, opt_conf_repo)
        if len(config.commissions) == 0:
            raise HTTPException(
                detail="Only a configuration with a solution can be frozen",
                status_code=http_statuses.HTTP_409_CONFLICT
            )
        config.frozen = True
        return config

    @post(urls.GRAD_SESSION_OPT_CONF_UNFREEZE, return_dto=OptConfDTO, status_code=http_statuses.HTTP_200_OK)
    async def unfreeze_configuration(self, sid: int, cid: int,
                                     opt_conf_repo: OptimizationConfigurationRepository
                                     ) -> OptimizationConfiguration:
        config = await get_opt_conf_raise(cid, sid, opt_conf_repo)
        config.frozen = False
        return config

    @get(urls.GRAD_SESSION_OPT_CONF_EXPORT)
    async def export_solution(self, sid: int, cid: int,
                              db_session: AsyncSession,
                              opt_conf_repo: OptimizationConfigurationRepository
                              ) -> Response[bytes]:
        """Excel file with the commissions of the solution: one row per student, plus the professors."""
        config = await get_opt_conf_raise(cid, sid, opt_conf_repo, load=[
            selectinload(OptimizationConfiguration.commissions).options(
                selectinload(SolutionCommission.professors),
                selectinload(SolutionCommission.students)
            )
        ])
        if len(config.commissions) == 0:
            raise HTTPException(
                detail="The configuration has no solution to export",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        content = await build_solution_xlsx(config, db_session)
        # Characters that aren't allowed in file names (e.g. "/" in a title) become "-"
        filename = re.sub(r'[\\/:*?"<>|]+', "-", f"commissioni-{config.session.title}-{config.title}") + ".xlsx"
        # Headers must be latin-1: an ASCII fallback, plus the UTF-8 name for browsers that support it (RFC 6266)
        ascii_name = filename.encode("ascii", "replace").decode().replace('"', "'").replace("?", "_")
        return Response(
            content,
            media_type=XLSX_MEDIA_TYPE,
            headers={"Content-Disposition": f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename)}'}
        )

    @get(urls.GRAD_SESSION_OPT_CONF_GET_COMPLETE)
    async def get_complete_configuration(self, sid: int, cid: int,
                                         grad_session_repository: GradSessionRepository,
                                         opt_conf_repo: OptimizationConfigurationRepository
                                         ) -> OptConfCompleteDTO:
        await check_gs_exists_raise(grad_session_repository, sid)
        config = await get_opt_conf_raise(cid, sid, opt_conf_repo, load=[
            selectinload(OptimizationConfiguration.commissions).options(
                selectinload(SolutionCommission.professors),
                selectinload(SolutionCommission.students)
            )
        ])
        return OptConfCompleteDTO.model_validate(config)

    @get(urls.GRAD_SESSION_OPT_CONF_SOLVE, status_code=http_statuses.HTTP_202_ACCEPTED)
    async def solve_configuration(self, session_id: int, config_id: int,
                                  grad_session_repository: GradSessionRepository,
                                  opt_conf_repo: OptimizationConfigurationRepository) -> None:
        logger.info(f"Received request to solve commission {session_id} with configuration {config_id}")

        await check_gs_exists_raise(grad_session_repository, session_id)
        config = await get_opt_conf_raise(config_id, session_id, opt_conf_repo)

        # First we check if the configuration has already been solved
        if len(config.commissions) > 0:
            logger.error(f"Configuration with ID {config_id} already solved")
            raise HTTPException(
                detail="Configuration already solved",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        if not config.online:
            raise HTTPException(
                detail="Optimization for configurations that are not online is deprecated.",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        # Then we check if the configuration is already running. If we're here, we're sure that we haven't saved a
        # solution yet.
        logger.debug(f"Locking the configuration {config_id}")
        if not await opt_conf_repo.acquire_lock(config_id):
            logger.error(f"Configuration with ID {config_id} is already being solved")
            raise HTTPException(
                detail=f"Configuration with ID {config_id} is already being solved",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        logger.debug(f"Setting up the optimization for session {session_id} and configuration {config_id}")
        cc_path = job_queue.job_dir(session_id, config_id)

        cc_path.mkdir(parents=True, exist_ok=True)

        try:
            config.create_dat_file(cc_path)

            with (cc_path / "val.xls").open('wb') as f:
                f.write(config.session.export_xls(config.durations))
        except Exception:
            logger.exception(f"Error during optimization files creation for session {session_id}, config {config_id}")
            if cc_path.exists():
                shutil.rmtree(cc_path)
                logger.debug(f"Deleted directory {cc_path} due to export error")

            raise

        # The job is committed together with the run_lock, so a locked configuration always has a job behind it.
        job_queue.enqueue(opt_conf_repo.session, config_id)
