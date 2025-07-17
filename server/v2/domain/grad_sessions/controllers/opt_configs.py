from advanced_alchemy.extensions.litestar import SQLAlchemyDTO
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from litestar.dto import DTOConfig, DTOData
from litestar.exceptions import HTTPException
import litestar.status_codes as http_statuses
from pydantic import BaseModel, ConfigDict, computed_field

from v2.db.models import OptimizationConfiguration, GradSession, Professor, Student, SolutionCommission, SolverEnum
from v2.domain.grad_sessions import urls
from v2.domain.grad_sessions.deps import SessionEntryRepository, OptimizationConfigurationRepository, \
    GradSessionRepository


class OptConfDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = DTOConfig(
        max_nested_depth=0
    )


class OptConfPatchDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = DTOConfig(
        max_nested_depth=0,
        partial=True,
        exclude={"id", "created_at", "updated_at", "session_id"}
    )


class OptConfListDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = DTOConfig(
        max_nested_depth=0,
        include={"session_id", "id", "title", "created_at", "updated_at"}
    )


class OptimizationLogDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    opt_config_id: int


class SolutionCommissionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_key: int
    morning: bool

    session_id: int
    opt_config_id: int

    # professors_ids: list[int]
    # students_ids: list[int]
    # @computed_field
    # def professors_ids(self) -> list[int]:
    #     # `self` is the ORM object (since from_attributes=True)
    #     return [p.id for p in self.professors]


class OptConfCompleteDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    session_id: int

    max_duration: int
    max_commissions_morning: int
    max_commissions_afternoon: int

    online: bool
    min_professor_number: int | None
    min_professor_number_masters: int | None
    max_professor_number: int | None

    solver: SolverEnum

    optimization_time_limit: int
    optimization_gap: float
    run_lock: bool

    optimization_log: OptimizationLogDTO | None
    commissions: list[None]


class OptimizationConfigurationController(Controller):
    """Optimization Configuration Controller"""

    tags = ["Graduation Sessions", "Optimization", "Configuration"]
    dependencies = {
        "grad_session_repository": Provide(GradSessionRepository.provide),
        "session_entry_repository": Provide(SessionEntryRepository.provide),
        "opt_conf_repo": Provide(OptimizationConfigurationRepository.provide)
    }

    @get(urls.GRAD_SESSION_OPT_CONF_NEW, return_dto=OptConfDTO)
    async def new_configuration(self,
                                sid: int,
                                grad_session_repository: GradSessionRepository,
                                opt_conf_repo: OptimizationConfigurationRepository) -> OptimizationConfiguration:
        if not await grad_session_repository.exists(GradSession.id == sid):
            raise HTTPException(
                detail="The specified Graduation Session does not exist",
                status_code=http_statuses.HTTP_404_NOT_FOUND
            )

        conf_count = await opt_conf_repo.count(OptimizationConfiguration.session_id == sid)

        conf = await opt_conf_repo.add(OptimizationConfiguration(session_id=sid))
        conf.title += f" {conf_count + 1}"

        return conf

    @get(urls.GRAD_SESSION_OPT_CONF_LIST, return_dto=OptConfListDTO)
    async def configuration_list(self,
                                 sid: int,
                                 grad_session_repository: GradSessionRepository,
                                 opt_conf_repo: OptimizationConfigurationRepository) -> list[OptimizationConfiguration]:
        if not await grad_session_repository.exists(GradSession.id == sid):
            raise HTTPException(
                detail="The specified Graduation Session does not exist",
                status_code=http_statuses.HTTP_404_NOT_FOUND
            )

        return await opt_conf_repo.list(OptimizationConfiguration.session_id == sid)

    @patch(urls.GRAD_SESSION_OPT_CONF_UPDATE, dto=OptConfPatchDTO, return_dto=OptConfDTO)
    async def update_configuration(self,
                                   sid: int,
                                   cid: int,
                                   data: DTOData[OptimizationConfiguration],
                                   opt_conf_repo: OptimizationConfigurationRepository
                                   ) -> OptimizationConfiguration:
        config: OptimizationConfiguration | None = await opt_conf_repo.get_one_or_none(
            OptimizationConfiguration.id == cid,
            OptimizationConfiguration.session_id == sid
        )
        if config is None:
            raise HTTPException("Configuration not found", status_code=http_statuses.HTTP_404_NOT_FOUND)

        return data.update_instance(config)

    @delete(urls.GRAD_SESSION_OPT_CONF_UPDATE, status_code=http_statuses.HTTP_200_OK)
    async def update_configuration(self,
                                   sid: int,
                                   cid: int,
                                   opt_conf_repo: OptimizationConfigurationRepository
                                   ) -> None:
        config: OptimizationConfiguration | None = await opt_conf_repo.get_one_or_none(
            OptimizationConfiguration.id == cid,
            OptimizationConfiguration.session_id == sid
        )
        if config is None:
            raise HTTPException("Configuration not found", status_code=http_statuses.HTTP_404_NOT_FOUND)

        await opt_conf_repo.delete(cid)

    @get(urls.GRAD_SESSION_OPT_CONF_GET_COMPLETE)
    async def get_complete_configuration(self,
                                         sid: int,
                                         cid: int,
                                         grad_session_repository: GradSessionRepository,
                                         opt_conf_repo: OptimizationConfigurationRepository
                                         ) -> OptConfCompleteDTO:
        if not await grad_session_repository.exists(GradSession.id == sid):
            raise HTTPException(
                detail="The specified Graduation Session does not exist",
                status_code=http_statuses.HTTP_404_NOT_FOUND
            )

        config: OptimizationConfiguration | None = await opt_conf_repo.get_one_or_none(
            OptimizationConfiguration.id == cid,
            OptimizationConfiguration.session_id == sid,
            # load=[
            #     OptimizationConfiguration.optimization_log,
            #     OptimizationConfiguration.commissions
            # ]
        )
        if config is None:
            raise HTTPException("Configuration not found", status_code=http_statuses.HTTP_404_NOT_FOUND)

        return OptConfCompleteDTO.model_validate(config)
