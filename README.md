# Automated Data Pipeline to Insert and Delete Records from a Database

## About the Repository

This repository contains a FastAPI backend and an HTML frontend for managing an Amazon sale report database. Users can:

- **Insert Records**: Add new records into the database.
- **Delete Records**: Remove records from the database using the `Order-Id` and `SKU`.
- **Get Records**: Retrieve specific records from the database using the `Order-Id` and `SKU`.
- **Analyze Data**: Perform analysis on the stored data.

The repository is hosted at [SoftIQo](https://softiqo-1.onrender.com/).

## Running the Repository via Docker

To run this project locally using Docker:

1. Clone the repository:

   ```bash
   git clone https://github.com/R1ch3rd/SoftIQo.git
   ```

2. Navigate to the project directory:

   ```bash
   cd SoftIQo
   ```

3. Start the application using Docker Compose:
   ```bash
   docker-compose up
   ```

This will set up the application and its dependencies, allowing you to use the database management and analysis tools provided in the project.
