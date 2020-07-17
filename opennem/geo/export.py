import decimal
import json
from datetime import date, datetime
from decimal import Decimal
from pprint import pprint

from geojson import Feature, FeatureCollection, Point, dumps
from smart_open import open
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import metadata

engine = db_connect()
session = sessionmaker(bind=engine)


UPLOAD_ARGS = {
    "ContentType": "application/json",
}


def wem_export():

    __sql = """
            select
            wf.code as duid,
            wf.capacity_maximum,
            wf.comissioned,
            wf.name as duid_name,
            ws.name,
            wf.fueltech_id as fueltech,
            f.label as fueltech_label,
            wf.status_id as status,
            fs.label as status_label,
            ws.code as station_code,
            ws.boundary as station_boundary,
            ST_AsGeoJSON(ws.geom) as station_point,
            ws.state,
            ws.postcode,
            ST_X(ws.geom),
            ST_Y(ws.geom),
            ST_AsText(ws.geom)
        from wem_station ws
        right join wem_facility wf on wf.station_id = ws.id
        join fueltech f on f.code = wf.fueltech_id
        join facility_status fs on fs.code = wf.status_id
        order by station_code asc
        --join wem_facility_scada wfs on wfs.facility_id = wf.id
    """

    query = __sql.format()
    features = []
    current_name = None
    current_station_code = None
    f = None

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:
            if current_station_code != row[9]:

                if f:
                    features.append(f)

                f = Feature()
                current_station_code = row[9]

                if row[11]:
                    f.geometry = Point((row[15], row[14]))

                f.properties = {
                    "station_id": row[0],
                    "station_code": row[9],
                    "network": "WEM",
                    "network_region": "WA",
                    "state": row[12],
                    "postcode": row[13],
                    "name": row[4],
                    "duid_data": [],
                }

            f.properties["duid_data"].append(
                {
                    "duid": row[0],
                    "comissioned_date": row[2].isoformat()
                    if type(row[2]) is datetime
                    else str(row[2]),
                    "fuel_tech": row[5],
                    "fuel_tech_label": row[6],
                    "status": row[7],
                    "status_label": row[8],
                    "registered_capacity": float(row[1]),
                }
            )

    if f:
        features.append(f)

    return features


def nem_export():
    __sql = """
        select
            wf.code as duid,
            wf.nameplate_capacity,
            wf.registered,
            wf.name as duid_name,
            ws.name,
            wf.fueltech_id as fueltech,
            f.label as fueltech_label,
            wf.status_id as status,
            fs.label as status_label,
            ws.code as station_code,
            ws.boundary as station_boundary,
            ST_AsGeoJSON(ws.geom) as station_point,
            ws.state,
            ws.postcode,
            ST_X(ws.geom),
            ST_Y(ws.geom),
            ST_AsText(ws.geom),
            ws.name_clean,
            ws.id,
            wf.region
        from nem_station ws
        join nem_facility wf on wf.station_id = ws.id
        join fueltech f on f.code = wf.fueltech_id
        join facility_status fs on fs.code = wf.status_id
        order by ws.id asc
    """
    query = __sql.format()
    features = []
    current_name = None
    current_station_code = None
    f = None

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:
            if current_station_code != row[18]:

                if f:
                    features.append(f)

                f = Feature()
                current_station_code = row[18]

                if row[11]:
                    f.geometry = Point((row[15], row[14]))

                f.properties = {
                    "station_id": row[0],
                    "station_code": row[9],
                    "network": "NEM",
                    "network_region": row[19],
                    "state": row[12],
                    "postcode": row[13],
                    "name": row[17] or row[4],
                    "duid_data": [],
                }

            f.properties["duid_data"].append(
                {
                    "duid": row[0],
                    "fuel_tech": row[5],
                    "commissioned_date": row[2].isoformat()
                    if type(row[2]) is datetime
                    else str(row[2]),
                    "fuel_tech_label": row[6],
                    "status": row[7],
                    "status_label": row[8],
                    "registered_capacity": float(row[1]) if row[1] else None,
                }
            )

    if f:
        features.append(f)

    return features


def wem_additionals():
    __sql = """
        select
            wf.code as duid,
            wf.capacity_maximum,
            wf.comissioned,
            wf.code as duid_name,
            wf.fueltech_id as fueltech,
            f.label as fueltech_label,
            wf.status_id as status,
            fs.label as status_label,
            ST_X(wf.geom),
            ST_Y(wf.geom),
            ST_AsText(wf.geom)
        from wem_facility wf
        join fueltech f on f.code = wf.fueltech_id
        join facility_status fs on fs.code = wf.status_id
        where wf.station_id is null and wf.geom is not null
    """
    query = __sql.format()
    features = []
    f = None

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:
            f = Feature()

            f.geometry = Point((row[9], row[8]))

            f.properties = {
                "station_id": row[0],
                "station_code": row[0],
                # "state": None,
                # "postcode": row[13],
                "name": row[2],
                "duid_data": [],
            }

            f.properties["duid_data"].append(
                {
                    "duid": row[0],
                    "fuel_tech": row[5],
                    "comissioned": row[2].isoformat()
                    if type(row[2]) is datetime
                    else str(row[2]),
                    "fuel_tech_label": row[6],
                    "status": row[7],
                    "status_label": row[8],
                    "registered_capacity": float(row[1]),
                }
            )

    if f:
        features.append(f)

    return features


def nem_additionals():
    __sql = """
        select
            wf.code as duid,
            wf.nameplate_capacity,
            wf.name,
            wf.registered,
            wf.code as duid_name,
            wf.fueltech_id as fueltech,
            f.label as fueltech_label,
            wf.status_id as status,
            fs.label as status_label,
            ST_X(wf.geom),
            ST_Y(wf.geom),
            ST_AsText(wf.geom)
        from nem_facility wf
        left join fueltech f on f.code = wf.fueltech_id
        left join facility_status fs on fs.code = wf.status_id
        where wf.station_id is null and wf.geom is not null
    """
    query = __sql.format()
    features = []
    f = None

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:
            f = Feature()

            f.geometry = Point((row[10], row[9]))

            f.properties = {
                "station_id": row[0],
                "station_code": row[0],
                # "state": None,
                # "postcode": row[13],
                "name": row[2],
                "duid_data": [],
            }

            f.properties["duid_data"].append(
                {
                    "duid": row[0],
                    "fuel_tech": row[5],
                    "comissioned": row[3].isoformat()
                    if type(row[3]) is datetime
                    else str(row[3]),
                    "fuel_tech_label": row[6],
                    "status": row[7],
                    "status_label": row[8],
                    "registered_capacity": float(row[1]),
                }
            )

    if f:
        features.append(f)

    return features


if __name__ == "__main__":
    wf = wem_export()
    nf = nem_export()
    # wf_a = wem_additionals()
    # nf_a = nem_additionals()

    crs = {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    }

    geoj = FeatureCollection(nf + wf, crs=crs, name="opennem")

    geoj["name"] = "nem_facilities"
    geoj["crs"] = crs

    # print(dumps(geoj, ))

    with open(
        "s3://data.opennem.org.au/v3/geo/au_facilities.json",
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        fh.write(dumps(geoj))
