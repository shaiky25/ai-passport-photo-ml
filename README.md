# 📸 AI Passport Photo Tool

A powerful, AI-driven application to convert any photo into a compliant U.S. passport photo. This tool uses a combination of computer vision for geometric analysis and a large language model for qualitative checks, ensuring your photo meets official government requirements.

![UI Screenshot](https://user-images.githubusercontent.com/12345/your-image-url-here.png) <!-- It's recommended to add a screenshot of the final UI -->

## ✨ Features

- **Smart Cropping & Sizing**: Automatically crops and resizes the photo to perfect 2x2 inch (600x600 pixels at 300 DPI) specifications.
- **Data-Driven Accuracy**: Includes a script to learn optimal cropping parameters from a set of sample photos, making the system progressively smarter.
- **Advanced Background Removal**: Utilizes the `rembg` deep learning model for highly accurate, clean background replacement.
- **AI Compliance Analysis**: Leverages the Anthropic (Claude) API to check for qualitative issues like shadows, non-neutral expressions, and obstructions.
- **HEIC Support**: Automatically handles and converts `.HEIC` images from iPhones and other devices.
- **Print-Ready Sheets**: Generate downloadable 4x6 or 5x7 print sheets with multiple passport photos and cutting guides.
- **Clear Feedback**: A dynamic UI provides a detailed compliance checklist, showing users exactly what, if anything, needs to be fixed.

## 🚀 Quick Start (Docker)

The easiest way to run the application is with Docker.

1.  **Build and run the containers:**
    ```bash
    docker-compose up --build
    ```
2.  **Access the application:**
    Open your browser and navigate to `http://localhost:3000`.

## 🛠️ Manual Local Setup

If you prefer to run the services manually, you will need Python 3.9+ and Node.js 16+.

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    *(Note: On macOS, you may need to install `libheif` first: `brew install libheif`)*
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    Create a file named `.env` in the `backend` directory and add your Anthropic API key:
    ```
    ANTHROPIC_API_KEY="your-api-key-here"
    ```
5.  **Run the server:**
    ```bash
    python app.py
    ```
    The backend will be running at `http://localhost:5000`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Run the development server:**
    ```bash
    npm start
    ```
    The frontend will be running at `http://localhost:3000`.

## 🧠 Improving Accuracy with the Learning Script

The application can learn from your own set of compliant passport photos to improve its cropping accuracy.

1.  **Add Sample Photos:**
    Place a collection of high-quality, compliant passport photos (20-30 images recommended) into the `backend/training_data` directory.
2.  **Run the Learning Script:**
    Navigate to the `backend` directory and run the script:
    ```bash
    # Make sure your virtual environment is activated
    python learn_from_samples.py
    ```
    This will generate a `learned_profile.json` file. The application will automatically use this profile on the next startup to perform more intelligent, data-driven cropping. You can re-run this script any time you add new photos to the `training_data` directory.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
