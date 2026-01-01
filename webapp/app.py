"""
Flask UI app: single page with an input form for viewing angles.
On submit, it calls a NeRF rendering backend (HTTP) to generate an image,
then displays that image and re-shows the form.

This file is ONLY the Flask webserver (UI + form). The NeRF model should run
as a separate service (e.g., Cloud Run or Vertex AI). The Flask app calls it.

Directory layout (recommended):
  webapp/
    app.py
    templates/
      index.html
    static/
      (optional; not required)
    requirements.txt

Deploy target for this Flask app: Google App Engine (standard or flexible),
or Cloud Run. Since you asked for "another google service to host the webserver"
while NeRF runs on GCP, App Engine is a straightforward choice for the UI webserver. :contentReference[oaicite:0]{index=0}
"""

import os
import uuid
import requests
from flask import Flask, request, render_template, url_for, Response, abort

app = Flask(__name__)

# Configure this to point at your NeRF rendering service.
# Example: https://nerf-renderer-xxxxx-uc.a.run.app
NERF_BACKEND_URL = os.environ.get("NERF_BACKEND_URL", "").rstrip("/")


@app.get("/")
def index():
    # Default values are optional
    return render_template(
        "index.html",
        azimuth_deg="45.0",
        polar_deg="60.0",
        elevation_deg="30.0",
        image_url=None,
        error=None,
    )


@app.post("/render")
def render():
    if not NERF_BACKEND_URL:
        return render_template(
            "index.html",
            azimuth_deg=request.form.get("azimuth_deg", ""),
            polar_deg=request.form.get("polar_deg", ""),
            elevation_deg=request.form.get("elevation_deg", ""),
            image_url=None,
            error="NERF_BACKEND_URL is not set on the server.",
        ), 500

    # Parse user inputs
    try:
        az = float(request.form["azimuth_deg"])
        pol = float(request.form["polar_deg"])
        elev = float(request.form["elevation_deg"])
    except Exception:
        return render_template(
            "index.html",
            azimuth_deg=request.form.get("azimuth_deg", ""),
            polar_deg=request.form.get("polar_deg", ""),
            elevation_deg=request.form.get("elevation_deg", ""),
            image_url=None,
            error="Invalid input. Please enter numeric degrees.",
        ), 400

    # Create a request id so the browser doesn't cache old images
    rid = str(uuid.uuid4())

    # Option A (recommended): ask backend to store result in GCS and return a signed URL
    # Option B (simple): backend returns PNG bytes; we proxy bytes via /image/<rid>
    #
    # This Flask app implements Option B: it stores the last request in a short-lived
    # in-memory dict keyed by rid. For production with multiple instances, prefer
    # backend->GCS signed URL instead of in-memory bytes.
    try:
        resp = requests.post(
            f"{NERF_BACKEND_URL}/render",
            json={"azimuth_deg": az, "polar_deg": pol, "elevation_deg": elev},
            timeout=300,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return render_template(
            "index.html",
            azimuth_deg=str(az),
            polar_deg=str(pol),
            elevation_deg=str(elev),
            image_url=None,
            error=f"Backend error: {e}",
        ), 502

    # Expect backend returns image/png bytes
    if resp.headers.get("content-type", "").split(";")[0].strip().lower() != "image/png":
        return render_template(
            "index.html",
            azimuth_deg=str(az),
            polar_deg=str(pol),
            elevation_deg=str(elev),
            image_url=None,
            error="Backend did not return image/png.",
        ), 502

    # Store bytes in memory (development/simple deployment)
    _IMAGE_CACHE[rid] = resp.content

    image_url = url_for("image", rid=rid)
    return render_template(
        "index.html",
        azimuth_deg=str(az),
        polar_deg=str(pol),
        elevation_deg=str(elev),
        image_url=image_url,
        error=None,
    )


# Very small in-memory cache (dev only). For production, use GCS or Redis.
_IMAGE_CACHE = {}


@app.get("/image/<rid>")
def image(rid: str):
    data = _IMAGE_CACHE.get(rid)
    if data is None:
        abort(404)
    # Optionally delete after one use to cap RAM:
    # del _IMAGE_CACHE[rid]
    return Response(data, mimetype="image/png")


if __name__ == "__main__":
    # Local dev: flask run is fine too, but this works standalone.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)

