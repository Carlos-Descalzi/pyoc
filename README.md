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

    # references a data access object by type hint
    _dao: UserDao 

    def get(self, id: int) -> User:
        return self._dao.get(id)

    def save(self, obj: User) -> User:
        return self._dao.save(obj)

    def find_all(self) -> List[User]:
        return self._dao.find_all()

    def delete(self, id: int):
        self._dao.delete(id)
```

## Method wrapper
```python
class LogWrapper(pyoc.Wrapper):
    def __call__(self, *args, **kwargs):

        arg_str_list = list(map(str, args)) + [f"{k}={v}" for k, v in kwargs.items()]

        obj_name = self.target.__self__.__class__.__name__
        method_name = self.target.__name__

        logging.info(f"invoked {obj_name}.{method_name}({','.join(arg_str_list)})")

        return self.next(*args, **kwargs)
```

## Endpoints
```python
class UsersResource(Resource):
    """
    Users endpoint
    """

    _user_service: UserService

    def get(self):
        users = self._user_service.find_all()
        return list(map(asdict, users))

class UserResource(Resource):

    # Reference user service by its interface.
    _user_service: UserService

    def get(self, id):
        user = self._user_service.get(id)
        if user:
            return asdict(user)

        abort(404)

```
## Put all together
```python

def build_context():
    ctx = pyoc.Context()
    ...
    ctx.add(SQLUserDaoImpl) # Add the user dao implementation
    ctx.add(UserServiceImpl) # Add the user service implementation
    ctx.wrap(UserServiceImpl, ".*", LogWrapper) # wrap service methods
    return ctx.build()


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    ctx = build_context()

    bp = pyoc.flask.BluePrint("main", __name__, "/", ctx)
    bp.add_endpoint(UsersResource, "/users", methods=["GET"])
    bp.add_endpoint(UserResource, "/users/<int:id>", methods=["GET"])
    app.register_blueprint(bp)
    
    app.run(debug=True)

```

Check out example folder for the complete code.
