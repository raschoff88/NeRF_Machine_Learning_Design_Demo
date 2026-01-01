# NeRF Viewer Web Application

This project implements an **end-to-end Neural Radiance Field (NeRF) pipeline**, starting from synthetic data generation in Blender, through NeRF training, and ending with a **web-deployable interactive viewer** where users can specify camera viewing angles and render novel views of a 3D scene.

The system is designed to be **scientifically correct**, **memory-efficient**, and **cloud-deployable** on Google Cloud Platform (GCP).

---

## Overview

The application consists of two services:

1. **NeRF Inference Service**  
   A backend service that loads a trained NeRF model checkpoint and renders images for arbitrary camera viewing angles.

2. **Flask Web UI**  
   A lightweight frontend that presents a form to the user, accepts viewing angles, sends them to the NeRF service, and displays the rendered image.

These services are deployed separately on GCP for scalability and clarity of responsibility.

---

## Repository Structure

```text
repo/
├── webapp/                # Flask UI (App Engine or Cloud Run)
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   ├── requirements.txt
│   └── app.yaml
│
├── nerf_service/          # NeRF inference backend (Cloud Run)
│   ├── service.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── training/              # (optional) training scripts
│
├── README.md

