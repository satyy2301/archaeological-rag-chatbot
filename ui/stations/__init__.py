"""Lab station renderers."""

from ui.stations.document_desk import render as render_document_desk
from ui.stations.artifact_station import render as render_artifact_station
from ui.stations.photo_archive import render as render_photo_archive
from ui.stations.spatial_room import render as render_spatial_room
from ui.stations.reference_library import render as render_reference_library
from ui.stations.output_office import render as render_output_office

STATION_RENDERERS = {
    "document_desk": render_document_desk,
    "artifact_station": render_artifact_station,
    "photo_archive": render_photo_archive,
    "spatial_room": render_spatial_room,
    "reference_library": render_reference_library,
    "output_office": render_output_office,
}
