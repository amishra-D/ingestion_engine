from src.features.Auth.Application.DTO.Input.LoginDTO import LoginInputDTO
from src.features.Auth.Application.DTO.Output.LoginResponseDTO import LoginResponseDTO
from src.features.Auth.Application.ports.LoginRepository import ILoginRepository
from src.features.Auth.Application.ports.TokenService import ITokenService
from src.features.Auth.Domain.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
)

class LoginUseCase:
    def __init__(
        self,
        repository: ILoginRepository,
        token_service: ITokenService,
    ):
        self.repository = repository
        self.token_service = token_service

    async def execute_login(self, request: LoginInputDTO) -> LoginResponseDTO:
        user = await self.repository.get_by_username(request.username)
        if user is None:
            raise InvalidCredentialsException()

        if not user.verify_password(request.password):
            raise InvalidCredentialsException()

        if not user.can_login():
            raise InactiveUserException()

        # Update last login time in database
        await self.repository.update_last_login(user.user_id)

        # Generate access token via the injected token service port
        access_token = self.token_service.generate_token(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
        )

        return LoginResponseDTO(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id,
            username=user.username,
            role=user.role,
        )