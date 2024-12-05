from Main import app  # Import the Flask app from your main script

if __name__ == "__main__":
    Server(app).run(host="0.0.0.0", port=5000)
