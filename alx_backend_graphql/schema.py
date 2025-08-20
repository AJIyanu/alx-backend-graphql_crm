import graphene

# Query is the entry point for all read operations in GraphQL
class Query(graphene.ObjectType):
    # A field in GraphQL: 'hello' that returns a string
    hello = graphene.String()

    # Resolver: defines how the value for the field is fetched
    def resolve_hello(root, info):
        return "Hello, GraphQL!"

# Schema ties everything together
schema = graphene.Schema(query=Query)
