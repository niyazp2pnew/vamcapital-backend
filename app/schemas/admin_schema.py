from typing import Dict
from pydantic import BaseModel


class InquiriesMetric(BaseModel):
    total: int
    new: int
    contacted: int
    converted: int
    by_source: Dict[str, int]


class JobsMetric(BaseModel):
    total: int
    active: int
    paused: int
    closed: int
    by_track: Dict[str, int]


class PipelineMetric(BaseModel):
    total_applications: int
    applied: int
    screening: int
    shortlisted: int
    interview_scheduled: int
    hired: int
    rejected: int


class PlatformStatsResponse(BaseModel):
    candidates_count: int
    companies_count: int
    inquiries: InquiriesMetric
    jobs: JobsMetric
    pipeline: PipelineMetric