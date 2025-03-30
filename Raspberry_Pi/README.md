# Raspberry Pi Edge Computing Projects

This repository contains different components and setups for Raspberry Pi, designed to test and integrate various hardware elements for **edge computing** applications. The projects explore individual hardware functionalities and then combine them into a single integrated system, with a focus on processing data locally on the Raspberry Pi rather than relying on cloud-based services.

The repository is organized into the following folders, each corresponding to different components or setups:

- **Image**: Raspberry Pi Webcam Streaming with Flask  
  This component sets up a **local webcam streaming server** on the Raspberry Pi using Flask. It includes a server-side script for capturing and streaming webcam video, designed to process and serve video data locally without needing cloud infrastructure.

- **Weight**: Raspberry Pi Load Cell with HX711  
  This component demonstrates how to interface a Raspberry Pi with an HX711 load cell amplifier to measure weight. The processing and calculation are done directly on the Raspberry Pi, ensuring that data does not need to be sent to the cloud for basic computations.

- **Integrated**: Raspberry Pi Project Setup with Breadboard, Button, HX711 Load Cell, and LED Light  
  This integrated setup combines the webcam, load cell, button, and LED light into a single edge computing system. It includes instructions on wiring and configuring the components, as well as how to expose the API using Ngrok for remote access, while still processing the data locally on the device.

## Methodology

Each component and the integrated system were developed with **modularity** and **simplicity** in mind, emphasizing **local data processing** and **minimizing cloud dependency**. 
The key design principles include:

### 1. **Raspberry Pi Webcam Streaming (image folder)**
- **Goal**: Set up a local, lightweight webcam streaming server.
- **Approach**: The video feed is processed locally on the Raspberry Pi, minimizing the need for cloud services and reducing latency for real-time streaming. Flask was used to create a simple, local web server that serves the video feed without needing an internet connection for basic operations.

### 2. **Raspberry Pi Load Cell with HX711 (weight folder)**
- **Goal**: Interface with a load cell to measure weight using the HX711 amplifier.
- **Approach**: The data from the load cell is processed locally on the Raspberry Pi, without sending weight readings to a remote server. This reduces data transmission overhead and allows for real-time weight measurement on the edge device, ensuring that the system is self-contained and independent of cloud services.
  
### 3. **Integrated Raspberry Pi Project (integrated folder)**
- **Goal**: Combine the webcam, load cell, button, and LED into a unified edge computing system.
- **Approach**: This integrated system demonstrates how edge devices can handle various tasks (video streaming, weight measurement, button press interaction, etc.) independently. Data from the webcam and load cell are processed locally, with Ngrok used to provide remote access to the device without needing cloud-based resources. This allows for real-time feedback and data processing at the edge of the network.

---

## Setup and Installation

For setup instructions and detailed information on each project, please refer to the README file in each respective project folder. Each folder contains a step-by-step guide for setting up, installing dependencies, and running the project on your Raspberry Pi.

