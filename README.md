# pyoc
An IOC/Dependency injection library similar to Spring IOC Container for python

# Installation
```bash
python3 setup.py install
```
# Example

## Service interface
```python

@dataclass
class User:
    id: int = None
    name: str = None

class UserService(metaclass=ABCMeta):
    @abstractmethod
    def get(self, id: int) -> User:
        pass

    @abstractmethod
    def save(self, obj: User) -> User:
        pass

    @abstractmethod
    def find_all(self) -> List[User]:
        pass

    @abstractmethod
    def delete(self, id: int):
        pass
```
## Service implementation
```python
class UserServiceImpl(UserService):

    # references a data access object
    _dao = pyoc.ref(UserDao)

    def get(self, id: int) -> User:
        return self._dao.get(id)

    def save(self, obj: User) -> User:
        return self._dao.save(obj)

    def find_all(self) -> List[User]:
        return self._dao.find_all()

    def delete(self, id: int):
        self._dao.delete(id)
```

## Endpoint
```python

class UserResource(Resource):

    # Reference user service by its interface.
    _user_service = pyoc.ref(UserService)

    def get(self, id):
        user = self._user_service.get(id)
        if user:
            return asdict(user)

        abort(404)

    def put(self, id):
        try:
            user_json = json.loads(request.data)
            user = self._user_service.get(id)
            user.name = user_json["name"]
            self._user_service.save(user)

            return None, 204
        except Exception as e:
            abort(500, str(e))

    def delete(self, id):
        self._user_service.delete(id)

        return None, 204

if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    bp = pyoc.flask.BluePrint("main", __name__, "/", ctx)
    bp.add_endpoint(UserResource, "/users/<int:id>", methods=["GET", "DELETE", "PUT"])
    app.register_blueprint(bp)
    
    app.run(debug=True)

```

Check out example folder for the complete code.
