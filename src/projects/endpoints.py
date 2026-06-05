from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from models import CreateProjectReq, ProjectOut, Project, EnvVar
from database import get_session
from sqlmodel import select
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from common.utils import verify_access_token, get_fernet


router = APIRouter(tags=["projects"])


def get_current_user(payload: dict = Depends(verify_access_token)) -> uuid.UUID:
    try:
        return uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")


@router.post("/projects", response_model=ProjectOut)
async def create_project(
    body: CreateProjectReq,
    owner_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    f = get_fernet()

    project = Project(
        name=body.name,
        owner_id=owner_id,
        git_url=body.git_url,
        port=body.port,
    )
    session.add(project)
    await session.flush()  # get project.id before adding env vars

    for ev in body.env_vars:
        session.add(
            EnvVar(
                project_id=project.id,
                key=ev.key,
                value=f.encrypt(ev.value.encode()).decode(),
            )
        )

    await session.commit()
    await session.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(
    owner_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Project).where(Project.owner_id == owner_id))
    return result.scalars().all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    project = await session.get(Project, project_id)
    if not project or project.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    project = await session.get(Project, project_id)
    if not project or project.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
