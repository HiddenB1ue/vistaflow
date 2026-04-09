from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

GeoStatus = Literal["all", "missing", "complete"]
GeoSourceFilter = Literal["all", "amap", "manual", "scraped"]
StationSortBy = Literal["id", "name", "geoUpdatedAt", "updatedAt"]
SortOrder = Literal["asc", "desc"]
TrainIsActiveFilter = Literal["all", "true", "false"]
TrainSortBy = Literal["id", "trainNo", "stationTrainCode", "updatedAt"]
StationGeoSource = Literal["amap", "manual", "scraped"]


class StationAdminItemResponse(BaseModel):
    id: int
    name: str
    telecode: str
    pinyin: str | None = None
    abbr: str | None = None
    areaName: str | None = None
    countryName: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    geoSource: str | None = None
    geoUpdatedAt: datetime | None = None
    updatedAt: datetime
    geoStatus: Literal["missing", "complete"]


class StationAdminListResponse(BaseModel):
    items: list[StationAdminItemResponse]
    page: int
    pageSize: int
    total: int
    totalPages: int


class StationGeoUpdateRequest(BaseModel):
    longitude: float | None
    latitude: float | None
    geoSource: StationGeoSource


class TrainAdminItemResponse(BaseModel):
    id: int
    trainNo: str
    stationTrainCode: str | None = None
    fromStation: str | None = None
    toStation: str | None = None
    totalNum: int | None = None
    isActive: bool
    updatedAt: datetime


class TrainAdminListResponse(BaseModel):
    items: list[TrainAdminItemResponse]
    page: int
    pageSize: int
    total: int
    totalPages: int


class TrainStopAdminItemResponse(BaseModel):
    stationNo: int
    stationName: str | None = None
    stationTrainCode: str | None = None
    arriveTime: str | None = None
    startTime: str | None = None
    runningTime: str | None = None
    arriveDayDiff: int | None = None
    arriveDayStr: str | None = None
    isStart: str | None = None
    startStationName: str | None = None
    endStationName: str | None = None
    trainClassName: str | None = None
    serviceType: str | None = None
    wzNum: str | None = None
    updatedAt: datetime
