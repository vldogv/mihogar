from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_admin, require_admin_or_encargado, get_current_user, TokenData, hash_password, hash_pin
from app.core.dependencies import get_usuario_repo, get_permiso_repo, get_zona_repo
from app.domain.repositories.interfaces import (
    UsuarioCasaRepository, PermisoZonaRepository, ZonaRepository,
)
from app.domain.entities.models import (
    UsuarioCasa, PermisoZona, RolUsuario, MetodoAcceso,
)
from app.domain.services.domain_services import PermisosService
from app.interfaces.schemas.dtos import (
    UsuarioResponse, UsuarioCreateRequest, UsuarioUpdateRequest,
    PermisoZonaDTO, PermisosRolResponse, MessageResponse,
)

router = APIRouter(tags=["Usuarios y Permisos"])


async def _build_usuario_response(
    u: UsuarioCasa,
    permiso_repo: PermisoZonaRepository,
    zona_repo: ZonaRepository,
    casa_id: str,
) -> UsuarioResponse:
    permisos = await permiso_repo.get_by_usuario(u.id)
    zonas = await zona_repo.get_by_casa(casa_id)
    zona_map = {z.id: z.nombre for z in zonas}

    zonas_ids = [p.zona_id for p in permisos]
    # Admin/Encargado → todas las zonas
    if u.rol in (RolUsuario.ADMINISTRADOR, RolUsuario.ENCARGADO):
        zonas_ids = [z.id for z in zonas]

    return UsuarioResponse(
        id=u.id, nombre=u.nombre, email=u.email,
        rol=str(u.rol), metodo_acceso=str(u.metodo_acceso),
        zonas_permitidas=[zona_map.get(zid, zid) for zid in zonas_ids],
        permisos=[
            PermisoZonaDTO(
                zona_id=p.zona_id, zona_nombre=zona_map.get(p.zona_id),
                puede_controlar=p.puede_controlar, puede_configurar=p.puede_configurar,
            )
            for p in permisos
        ],
    )


@router.get("/casas/{casa_id}/usuarios", response_model=list[UsuarioResponse])
async def get_usuarios(
    casa_id: str,
    current_user: TokenData = Depends(require_admin_or_encargado),
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
    permiso_repo: PermisoZonaRepository = Depends(get_permiso_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    usuarios = await usuario_repo.get_by_casa(casa_id)
    results = []
    for u in usuarios:
        resp = await _build_usuario_response(u, permiso_repo, zona_repo, casa_id)
        results.append(resp)
    return results


@router.post("/casas/{casa_id}/usuarios", response_model=UsuarioResponse)
async def create_usuario(
    casa_id: str,
    body: UsuarioCreateRequest,
    current_user: TokenData = Depends(require_admin_or_encargado),
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
    permiso_repo: PermisoZonaRepository = Depends(get_permiso_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    try:
        rol = RolUsuario(body.rol)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Rol inválido: {body.rol}")

    if rol == RolUsuario.ADMINISTRADOR:
        raise HTTPException(status_code=400, detail="No se puede crear otro administrador")
    # Encargado solo puede crear usuarios normales
    if current_user.rol == "encargado" and rol != RolUsuario.USUARIO:
        raise HTTPException(status_code=403, detail="Encargado solo puede crear usuarios normales")

    # Determinar método de acceso
    if body.pin:
        metodo = MetodoAcceso.PIN
        pw_hash = None
        pin_h = hash_pin(body.pin)
    elif body.email and body.password:
        metodo = MetodoAcceso.EMAIL
        pw_hash = hash_password(body.password)
        pin_h = None
    else:
        raise HTTPException(status_code=400, detail="Se requiere email+password o PIN")

    # Check email duplicado en esta casa
    if body.email:
        existing = await usuario_repo.get_by_email_and_casa(body.email, casa_id)
        if existing:
            raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email en esta casa")

    usuario = UsuarioCasa(
        casa_id=casa_id, nombre=body.nombre, email=body.email,
        password_hash=pw_hash, pin_hash=pin_h, rol=rol, metodo_acceso=metodo,
    )
    created = await usuario_repo.create(usuario)

    # Asignar permisos de zona si es rol "usuario"
    if rol == RolUsuario.USUARIO and body.zonas_permitidas:
        permisos = [
            PermisoZona(usuario_id=created.id, zona_id=zid, puede_controlar=True, puede_configurar=False)
            for zid in body.zonas_permitidas
        ]
        await permiso_repo.set_permisos(created.id, permisos)

    return await _build_usuario_response(created, permiso_repo, zona_repo, casa_id)


@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: str,
    body: UsuarioUpdateRequest,
    current_user: TokenData = Depends(require_admin),
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
    permiso_repo: PermisoZonaRepository = Depends(get_permiso_repo),
    zona_repo: ZonaRepository = Depends(get_zona_repo),
):
    usuario = await usuario_repo.get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if usuario.rol == RolUsuario.ADMINISTRADOR:
        raise HTTPException(status_code=400, detail="No se puede modificar al administrador")
    # Encargado solo puede editar zonas de usuarios normales
    if current_user.rol == "encargado":
        if str(usuario.rol) != "usuario":
            raise HTTPException(status_code=403, detail="Solo puedes editar usuarios normales")
        if body.rol is not None or body.nombre is not None or body.email is not None:
            raise HTTPException(status_code=403, detail="Solo puedes editar las zonas permitidas")

    if body.nombre is not None:
        usuario.nombre = body.nombre
    if body.email is not None:
        usuario.email = body.email
    if body.rol is not None:
        try:
            usuario.rol = RolUsuario(body.rol)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Rol inválido: {body.rol}")

    updated = await usuario_repo.update(usuario)

    # Actualizar zonas permitidas
    if body.zonas_permitidas is not None:
        permisos = [
            PermisoZona(usuario_id=usuario_id, zona_id=zid, puede_controlar=True, puede_configurar=False)
            for zid in body.zonas_permitidas
        ]
        await permiso_repo.set_permisos(usuario_id, permisos)

    return await _build_usuario_response(updated, permiso_repo, zona_repo, usuario.casa_id)


@router.delete("/usuarios/{usuario_id}", response_model=MessageResponse)
async def delete_usuario(
    usuario_id: str,
    current_user: TokenData = Depends(require_admin),
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
    permiso_repo: PermisoZonaRepository = Depends(get_permiso_repo),
):
    usuario = await usuario_repo.get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.rol == RolUsuario.ADMINISTRADOR:
        raise HTTPException(status_code=400, detail="No se puede eliminar al administrador")

    await permiso_repo.delete_by_usuario(usuario_id)
    await usuario_repo.delete(usuario_id)
    return MessageResponse(message="Usuario eliminado")


@router.get("/casas/{casa_id}/permisos-rol", response_model=PermisosRolResponse)
async def get_permisos_por_rol(
    casa_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    return PermisosRolResponse(
        administrador=sorted(PermisosService.get_permisos(RolUsuario.ADMINISTRADOR)),
        encargado=sorted(PermisosService.get_permisos(RolUsuario.ENCARGADO)),
        usuario=sorted(PermisosService.get_permisos(RolUsuario.USUARIO)),
    )


@router.put("/usuarios/{usuario_id}/password", response_model=MessageResponse)
async def change_password(
    usuario_id: str,
    body: dict,
    current_user: TokenData = Depends(require_admin),
    usuario_repo: UsuarioCasaRepository = Depends(get_usuario_repo),
):
    """Solo admin puede cambiar contraseñas."""
    usuario = await usuario_repo.get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.rol == RolUsuario.ADMINISTRADOR:
        raise HTTPException(status_code=400, detail="No se puede modificar al administrador")
    new_password = body.get("password")
    new_pin = body.get("pin")
    if new_password:
        usuario.password_hash = hash_password(new_password)
    elif new_pin:
        usuario.pin_hash = hash_pin(new_pin)
    else:
        raise HTTPException(status_code=400, detail="Se requiere password o pin")
    await usuario_repo.update(usuario)
    return MessageResponse(message="Contraseña actualizada")
