from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.analytics import Athena, Glue
from diagrams.aws.network import ELB

with Diagram("Complex Serverless Architecture", show=False):
    with Cluster("Serverless Services"):
        event_processing = Lambda("Event Processing")
        serverless_backend = Lambda("Serverless Backend")
        etl = Lambda("ETL")
        db = Dynamodb("NoSQL Database")
        athena = Athena("Query Service")
        glue = Glue("Data Integration")
    
    elb = ELB("Elastic Load Balancer")
    
    event_processing >> db
    serverless_backend >> db
    etl >> db
    athena >> db
    glue >> db
    db >> elb