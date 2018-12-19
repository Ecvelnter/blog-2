from app import create_app,db
from app.models import User,Microblog,Blog,Category,Favourite


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db':db,'User':User,'Microblog':Microblog,'Blog':Blog,'Category':Category,'Favourite':Favourite}