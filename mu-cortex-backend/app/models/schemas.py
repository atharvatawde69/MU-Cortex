from pydantic import BaseModel


class Subject(BaseModel):
    id: str
    name: str
    code: str
    scheme_id: str
    semester: int
    branch: str


class VideoResource(BaseModel):
    id: str
    topic_id: str
    youtube_url: str
    title: str
    engagement_score: int

