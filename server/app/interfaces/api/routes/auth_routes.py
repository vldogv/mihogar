from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import (
    verify_password, verify_pin, create_access_token, get_current_user, TokenData,
)
from app.core.dependencies import get_owner_repo, get_usuario_repo, get_casa_repo, get_permiso_repo
from app.domain.repositories.interfaces import (
    OwnerRepository, UsuarioCasaRepository, CasaRepository, PermisoZonaRepository,
)
from app.interfaces.schemas.dtos import (
    LoginRequest, LoginPinRequest, SelectCasaRequest,
    TokenResponse, LoginOwnerResponse, CasaSimple,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    body: LoginRequest,
    owner_repo: OwnerRepository = Depends(get_owner_repo),
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
    casa_repo: CasaRepository = Depends(get_casa_repo),
    permiso_repo: PermisoZonaRepository = Depends(get_permiso_repo),
):
    """
    Login unificado.
    1. Busca en owners → si encuentra, devuelve lista de casas.
    2. Si no es owner, busca en usuarios_casa → devuelve token con casa_id.
    """
    # Intentar como owner
    owner = await owner_repo.get_by_email(body.email)
    if owner and verify_password(body.password, owner.password_hash):
        casas = await casa_repo.get_by_owner(owner.id)
        token = create_access_token({
            "owner_id": owner.id,
            "email": owner.email,
            "rol": "owner",
        })
        return LoginOwnerResponse(
            access_token=token,
            nombre=owner.nombre,
            casas=[
                CasaSimple(id=c.id, nombre=c.nombre, direccion=c.direccion)
                for c in casas
            ],
        )

    # Intentar como usuario de casa
    usuario = await usuario_repo.get_by_email(body.email)
    if usuario and usuario.password_hash and verify_password(body.password, usuario.password_hash):
        # Obtener zonas permitidas
        permisos = await permiso_repo.get_by_usuario(usuario.id)
        zonas_ids = [str(p.zona_id) for p in permisos]
        token = create_access_token({
            "usuario_id": usuario.id,
            "casa_id": usuario.casa_id,
            "email": usuario.email,
            "rol": str(usuario.rol),
            "zonas_permitidas": zonas_ids,
        })
        return TokenResponse(
            access_token=token,
            rol=str(usuario.rol),
            nombre=usuario.nombre,
            zonas_permitidas=zonas_ids,
            casa_id=usuario.casa_id,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
    )


@router.post("/pin", response_model=TokenResponse)
async def login_pin(
    body: LoginPinRequest,
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
):
    """Login con PIN (para niños, adultos mayores)."""
    usuarios = await usuario_repo.get_by_pin_and_casa(body.pin, body.casa_id)
    for u in usuarios:
        if u.pin_hash and verify_pin(body.pin, u.pin_hash):
            token = create_access_token({
                "usuario_id": u.id,
                "casa_id": u.casa_id,
                "rol": u.rol.value,
            })
            return TokenResponse(
                access_token=token,
                rol=u.rol.value,
                nombre=u.nombre,
                casa_id=u.casa_id,
            )
    raise HTTPException(status_code=401, detail="PIN inválido")


@router.post("/select-casa", response_model=TokenResponse)
async def select_casa(
    body: SelectCasaRequest,
    current_user: TokenData = Depends(get_current_user),
    casa_repo: CasaRepository = Depends(get_casa_repo),
    permiso_repo: PermisoZonaRepository = Depends(get_permiso_repo),
    owner_repo: OwnerRepository = Depends(get_owner_repo),
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
):
    """Owner selecciona una casa. Genera nuevo token con casa_id."""
    if not current_user.owner_id:
        raise HTTPException(status_code=403, detail="Solo owners pueden seleccionar casa")

    casa = await casa_repo.get_by_id(body.casa_id)
    if not casa or casa.owner_id != current_user.owner_id:
        raise HTTPException(status_code=404, detail="Casa no encontrada")

    owner = await owner_repo.get_by_id(current_user.owner_id)

    token = create_access_token({
        "owner_id": current_user.owner_id,
        "casa_id": body.casa_id,
        "email": current_user.email,
        "rol": "administrador",
    })
    return TokenResponse(
        access_token=token,
        rol="administrador",
        nombre=owner.nombre if owner else "Admin",
        casa_id=body.casa_id,
    )


@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    return {
        "owner_id": current_user.owner_id,
        "usuario_id": current_user.usuario_id,
        "casa_id": current_user.casa_id,
        "rol": current_user.rol,
        "email": current_user.email,
    }
