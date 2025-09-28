# Generated manually to accompany energy_pb2.py for gRPC services.
# Mirrors the structure produced by grpc_tools.protoc.

import grpc
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

from . import energy_pb2 as energy__pb2


class SolarAgentStub(object):
    def __init__(self, channel: grpc.Channel):
        self.Health = channel.unary_unary(
            "/energy.SolarAgent/Health",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.HealthResponse.FromString,
        )
        self.GetStatus = channel.unary_unary(
            "/energy.SolarAgent/GetStatus",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.SolarStatus.FromString,
        )
        self.UpdateProduction = channel.unary_unary(
            "/energy.SolarAgent/UpdateProduction",
            request_serializer=energy__pb2.ProductionUpdate.SerializeToString,
            response_deserializer=energy__pb2.SolarStatus.FromString,
        )


class SolarAgentServicer(object):
    async def Health(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def GetStatus(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def UpdateProduction(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_SolarAgentServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Health": grpc.unary_unary_rpc_method_handler(
            servicer.Health,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.HealthResponse.SerializeToString,
        ),
        "GetStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatus,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.SolarStatus.SerializeToString,
        ),
        "UpdateProduction": grpc.unary_unary_rpc_method_handler(
            servicer.UpdateProduction,
            request_deserializer=energy__pb2.ProductionUpdate.FromString,
            response_serializer=energy__pb2.SolarStatus.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("energy.SolarAgent", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


class BatteryAgentStub(object):
    def __init__(self, channel: grpc.Channel):
        self.Health = channel.unary_unary(
            "/energy.BatteryAgent/Health",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.HealthResponse.FromString,
        )
        self.GetStatus = channel.unary_unary(
            "/energy.BatteryAgent/GetStatus",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.BatteryStatus.FromString,
        )
        self.UpdateMeasurement = channel.unary_unary(
            "/energy.BatteryAgent/UpdateMeasurement",
            request_serializer=energy__pb2.BatteryMeasurement.SerializeToString,
            response_deserializer=energy__pb2.BatteryStatus.FromString,
        )
        self.ApplyControl = channel.unary_unary(
            "/energy.BatteryAgent/ApplyControl",
            request_serializer=energy__pb2.BatteryControl.SerializeToString,
            response_deserializer=energy__pb2.BatteryStatus.FromString,
        )


class BatteryAgentServicer(object):
    async def Health(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def GetStatus(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def UpdateMeasurement(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def ApplyControl(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_BatteryAgentServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Health": grpc.unary_unary_rpc_method_handler(
            servicer.Health,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.HealthResponse.SerializeToString,
        ),
        "GetStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatus,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.BatteryStatus.SerializeToString,
        ),
        "UpdateMeasurement": grpc.unary_unary_rpc_method_handler(
            servicer.UpdateMeasurement,
            request_deserializer=energy__pb2.BatteryMeasurement.FromString,
            response_serializer=energy__pb2.BatteryStatus.SerializeToString,
        ),
        "ApplyControl": grpc.unary_unary_rpc_method_handler(
            servicer.ApplyControl,
            request_deserializer=energy__pb2.BatteryControl.FromString,
            response_serializer=energy__pb2.BatteryStatus.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("energy.BatteryAgent", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


class VehicleAgentStub(object):
    def __init__(self, channel: grpc.Channel):
        self.Health = channel.unary_unary(
            "/energy.VehicleAgent/Health",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.HealthResponse.FromString,
        )
        self.GetStatus = channel.unary_unary(
            "/energy.VehicleAgent/GetStatus",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.VehicleStatus.FromString,
        )
        self.UpdateMeasurement = channel.unary_unary(
            "/energy.VehicleAgent/UpdateMeasurement",
            request_serializer=energy__pb2.VehicleMeasurement.SerializeToString,
            response_deserializer=energy__pb2.VehicleStatus.FromString,
        )
        self.ApplyControl = channel.unary_unary(
            "/energy.VehicleAgent/ApplyControl",
            request_serializer=energy__pb2.VehicleControl.SerializeToString,
            response_deserializer=energy__pb2.VehicleStatus.FromString,
        )


class VehicleAgentServicer(object):
    async def Health(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def GetStatus(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def UpdateMeasurement(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def ApplyControl(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_VehicleAgentServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Health": grpc.unary_unary_rpc_method_handler(
            servicer.Health,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.HealthResponse.SerializeToString,
        ),
        "GetStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatus,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.VehicleStatus.SerializeToString,
        ),
        "UpdateMeasurement": grpc.unary_unary_rpc_method_handler(
            servicer.UpdateMeasurement,
            request_deserializer=energy__pb2.VehicleMeasurement.FromString,
            response_serializer=energy__pb2.VehicleStatus.SerializeToString,
        ),
        "ApplyControl": grpc.unary_unary_rpc_method_handler(
            servicer.ApplyControl,
            request_deserializer=energy__pb2.VehicleControl.FromString,
            response_serializer=energy__pb2.VehicleStatus.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("energy.VehicleAgent", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


class LoadAgentStub(object):
    def __init__(self, channel: grpc.Channel):
        self.Health = channel.unary_unary(
            "/energy.LoadAgent/Health",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.HealthResponse.FromString,
        )
        self.GetStatus = channel.unary_unary(
            "/energy.LoadAgent/GetStatus",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.LoadStatus.FromString,
        )
        self.UpdateLoad = channel.unary_unary(
            "/energy.LoadAgent/UpdateLoad",
            request_serializer=energy__pb2.LoadMeasurement.SerializeToString,
            response_deserializer=energy__pb2.LoadStatus.FromString,
        )
        self.ApplyShedding = channel.unary_unary(
            "/energy.LoadAgent/ApplyShedding",
            request_serializer=energy__pb2.LoadSheddingRequest.SerializeToString,
            response_deserializer=energy__pb2.LoadStatus.FromString,
        )


class LoadAgentServicer(object):
    async def Health(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def GetStatus(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def UpdateLoad(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def ApplyShedding(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_LoadAgentServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Health": grpc.unary_unary_rpc_method_handler(
            servicer.Health,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.HealthResponse.SerializeToString,
        ),
        "GetStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatus,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.LoadStatus.SerializeToString,
        ),
        "UpdateLoad": grpc.unary_unary_rpc_method_handler(
            servicer.UpdateLoad,
            request_deserializer=energy__pb2.LoadMeasurement.FromString,
            response_serializer=energy__pb2.LoadStatus.SerializeToString,
        ),
        "ApplyShedding": grpc.unary_unary_rpc_method_handler(
            servicer.ApplyShedding,
            request_deserializer=energy__pb2.LoadSheddingRequest.FromString,
            response_serializer=energy__pb2.LoadStatus.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("energy.LoadAgent", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


class CentralCoordinatorStub(object):
    def __init__(self, channel: grpc.Channel):
        self.Health = channel.unary_unary(
            "/energy.CentralCoordinator/Health",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.HealthResponse.FromString,
        )
        self.GetStatus = channel.unary_unary(
            "/energy.CentralCoordinator/GetStatus",
            request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            response_deserializer=energy__pb2.SystemStatus.FromString,
        )
        self.Coordinate = channel.unary_unary(
            "/energy.CentralCoordinator/Coordinate",
            request_serializer=energy__pb2.CoordinateRequest.SerializeToString,
            response_deserializer=energy__pb2.CoordinateResponse.FromString,
        )


class CentralCoordinatorServicer(object):
    async def Health(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def GetStatus(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    async def Coordinate(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_CentralCoordinatorServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Health": grpc.unary_unary_rpc_method_handler(
            servicer.Health,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.HealthResponse.SerializeToString,
        ),
        "GetStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatus,
            request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            response_serializer=energy__pb2.SystemStatus.SerializeToString,
        ),
        "Coordinate": grpc.unary_unary_rpc_method_handler(
            servicer.Coordinate,
            request_deserializer=energy__pb2.CoordinateRequest.FromString,
            response_serializer=energy__pb2.CoordinateResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("energy.CentralCoordinator", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


__all__ = (
    "SolarAgentStub",
    "SolarAgentServicer",
    "add_SolarAgentServicer_to_server",
    "BatteryAgentStub",
    "BatteryAgentServicer",
    "add_BatteryAgentServicer_to_server",
    "VehicleAgentStub",
    "VehicleAgentServicer",
    "add_VehicleAgentServicer_to_server",
    "LoadAgentStub",
    "LoadAgentServicer",
    "add_LoadAgentServicer_to_server",
    "CentralCoordinatorStub",
    "CentralCoordinatorServicer",
    "add_CentralCoordinatorServicer_to_server",
)
