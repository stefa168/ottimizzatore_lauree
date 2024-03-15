# Ottimizzatore Lauree 
_(graduation day optimizer)

This is a web application built with Svelte and TypeScript, and uses Python for backend services. The application is
designed to handle optimization configurations. It requires a CPLEX license to run the optimization algorithm. The code
will be adapted to accept also other optimization solvers.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing
purposes.

### Prerequisites

- Node.js and npm
- Python and pip

### Installing

1. Clone the repository
    ```bash
    git clone https://github.com/stefa168/ottimizzatore_lauree.git
    ```

2. Install Node.js dependencies
    ```bash
    cd ottimizzatore_lauree/web
    npm install
    ```

3. Install Python dependencies
    ```bash
    cd ottimizzatore_lauree/server
    pip install -r requirements.txt
    ```

## Running the Application

1. Start the backend server
    ```bash
    cd ottimizzatore_lauree/server
    python server.py
    ```

2. Start the frontend server
    ```bash
    cd ottimizzatore_lauree/web
    npm run dev
    ```

## Built With

- [Svelte](https://svelte.dev/) - The web framework used
- [TypeScript](https://www.typescriptlang.org/) - The language for web development
- [Python](https://www.python.org/) - The language for backend services

## Authors

- **stefa168** - *Initial work*

## License

This project is licensed under the GNU GPL3 License - see the [LICENSE.md](LICENSE.md) file for details