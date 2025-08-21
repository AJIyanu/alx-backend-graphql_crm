import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# Query is the entry point for all read operations in GraphQL
class Query(CRMQuery, graphene.ObjectType):
    # A field in GraphQL: 'hello' that returns a string
    hello = graphene.String()

    # Resolver: defines how the value for the field is fetched
    def resolve_hello(root, info):
        return "Hello, GraphQL!"
    
class Mutation(CRMMutation, graphene.ObjectType):
    pass

# Schema ties everything together
schema = graphene.Schema(query=Query, mutation=Mutation)