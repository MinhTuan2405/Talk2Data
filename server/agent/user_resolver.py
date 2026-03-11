from vanna.core.user import UserResolver, User, RequestContext


class SimpleUserResolver(UserResolver):
    """Resolve user from request context (cookies/headers).

    Replace this with JWT/OAuth logic in production.
    """

    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie("vanna_email") or "guest@example.com"
        group = "admin" if user_email == "admin@example.com" else "user"
        return User(id=user_email, email=user_email, group_memberships=[group])
