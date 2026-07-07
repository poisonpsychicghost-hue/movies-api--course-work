from flask import jsonify, request

philosophers = []
next_philosopher_id = 1

def register_philosophers_routes(app, error_response):

    @app.get("/philosophers")
    def list_philosophers():
        return jsonify(philosophers), 200

    @app.get("/philosophers/<int:philosopher_id>")
    def get_philosopher(philosopher_id):
        for p in philosophers:
            if p["id"] == philosopher_id:
                return jsonify(p), 200
            return error_response("Not Found", f"Philosopher with id {philosopher_id} Not Found", 404)

    @app.post("/philosophers")
    def create_philosphers():
        global next_philosopher_id

        if not request.is_json:
            return error_response("Bad Request", "Not valid JSON", 400)
        
        data = request.get_json()

        required_fields = ["name", "approx_year_born", "is_living", "school_of_thought", "famous_quote"]

        for field in required_fields:
            if field not in data:
                return error_response(
                    "Bad Request",
                    f"Missing required field: {field}", 400)
        for field in ["name", "school_of_thought", "famous_quote"]:
            value = data.get(field)
            if not isinstance(value, str) or value.strip() == "":
                return error_response("Bad Request",
                    f"Field '{field}' must be a non-empty string",
                400)
        if not isinstance(data.get("approx_year_born"), int):
            return error_response(
                "Bad Request",
                "Field 'year' must be an integer",
                400)
        if not isinstance(data.get("is_living"), bool):
            return error_response(
                "Bad Request",
                "Field 'watched' must be a boolean", 400)
        
        new_philosopher_id = next_philosopher_id
        next_philosopher_id += 1

        philosopher = {
            "id": new_philosopher_id,
            "name": data["name"],
            "approx_year_born": data["approx_year_born"],
            "is_living": data["is_living"],
            "school_of_thought": data["school_of_thought"],
            "famous_quote": data["famous_quote"]
        }

        philosophers.append(philosopher)

        return jsonify(philosopher), 201
 
    @app.put("/philosophers/<int:philosopher_id>")
    def update_philosopher(philosopher_id):
        philosopher = next((p for p in philosophers if p["id"] == philosopher_id), None)
        if philosopher is None:
            return error_response(
                "Not Found",
                f"Movie with id {id} not found.",
                404
            )
        
        if not request.is_json:
            return error_response("Bad Request", "Not valid JSON", 400)

        data = request.get_json()

        required_fields = ["name", "approx_year_born", "is_living", "school_of_thought", "famous_quote"]

        for field in required_fields:
            if field not in data:
                return error_response(
                    "Bad Request",
                    f"Missing required field: {field}", 400)
        for field in ["name", "school_of_thought", "famous_quote"]:
            value = data.get(field)
            if not isinstance(value, str) or value.strip() == "":
                return error_response("Bad Request",
                    f"Field '{field}' must be a non-empty string",
                400)
        if not isinstance(data.get("approx_year_born"), int):
            return error_response(
                "Bad Request",
                "Field 'year' must be an integer",
                400)
        if not isinstance(data.get("is_living"), bool):
            return error_response(
                "Bad Request",
                "Field 'watched' must be a boolean", 400)
        
        philosopher["name"] = data["name"]
        philosopher["approx_year_born"] = data["approx_year_born"]
        philosopher["is_living"] = data["is_living"]
        philosopher["school_of_thought"] = data["school_of_thought"]
        philosopher["famous_quote"] = data["famous_quote"]

        return jsonify(philosopher), 200
    
    @app.delete("/philosophers/<int:philosopher_id>")
    def delete_philosopher(philosopher_id):

        philosopher = next((p for p in philosophers if p["id"] == philosopher_id), None)

        if philosopher is None:
            return error_response("Not Found",
            f"Philosopher with id {id} not found.", 404)
        
        philosophers.remove(philosopher)
        return "", 204
