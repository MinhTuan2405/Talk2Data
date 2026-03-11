from vanna.core.user import UserResolver, User, RequestContext

from core.sercurity import decode_token


class JWTUserResolver(UserResolver):
    """Resolve user from JWT token set by the existing auth system."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        token = request_context.get_header("Authorization")

        if token and token.startswith("Bearer "):
            token = token[7:]
            payload = decode_token(token)

            if payload:
                user_id = payload.get("sub", "guest")
                user_email = payload.get("email", f"{user_id}@local")
                group = "admin" if payload.get("role") == "admin" else "user"
                return User(
                    id=user_id,
                    email=user_email,
                    group_memberships=[group],
                )

        return User(id="guest", email="guest@local", group_memberships=["user"])
