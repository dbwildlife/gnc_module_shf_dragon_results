#!/usr/bin/python3
# -*- coding: utf-8 -*-


from geoalchemy2 import Geometry
from server import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import deferred
from utils_flask_sqla_geo.serializers import geoserializable, serializable

# @serializable
# @geoserializable
# class SiteModel(TimestampMixinModel, ObserverMixinModel, db.Model):
#     """Table des sites"""

#     __tablename__ = "t_sites"
#     __table_args__ = {"schema": "gnc_sites"}
#     id_site = db.Column(db.Integer, primary_key=True, unique=True)
#     uuid_sinp = db.Column(UUID(as_uuid=True), nullable=False, unique=True)
#     id_program = db.Column(
#         db.Integer, db.ForeignKey(ProgramsModel.id_program), nullable=False
#     )
#     name = db.Column(db.String(250))
#     id_type = db.Column(
#         db.Integer, db.ForeignKey(SiteTypeModel.id_typesite), nullable=False
#     )
#     geom = db.Column(Geometry("POINT", 4326))

#     def __repr__(self):
#         return "<Site {0}>".format(self.id_site)


@serializable
class BibAreasTypes(db.Model):
    __tablename__ = "bib_areas_types"
    __table_args__ = {"schema": "ref_geo"}
    id_type = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.Unicode)
    type_code = db.Column(db.Unicode)
    type_desc = db.Column(db.Unicode)


@serializable
@geoserializable(geoCol="geom", idCol="id_area")
class LAreas(db.Model):
    """Table des zonages"""

    __tablename__ = "l_areas"
    __table_args__ = {"schema": "ref_geo"}
    id_area = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.Integer, ForeignKey("ref_geo.bib_areas_types.id_type"))
    area_name = db.Column(db.Unicode)
    area_code = db.Column(db.Unicode)
    geom = db.Column(Geometry("GEOMETRY"))
    centroid = db.Column(Geometry("POINT"))
    geojson_4326 = deferred(db.Column(db.Unicode))
    enable = db.Column(db.Boolean)
