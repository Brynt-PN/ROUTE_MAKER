from django.test import TestCase

from accounts.models import Organization
from RMapp.models import DispatchBatch, DispatchStop, Origin


class RouteGenerationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Logistics",
            country_code="pe",
            max_stops_per_route=4,
        )

    def _create_origin_with_nodes(self, nodes):
        dispatch_batch = DispatchBatch.objects.create(
            organization=self.organization,
            origin_address="Base de prueba",
            total_stops=len(nodes),
        )
        origin = Origin.objects.create(
            name="Base de prueba",
            lat="-12.046400",
            lon="-77.042800",
            organization=self.organization,
            dispatch_batch=dispatch_batch,
        )
        for index, (name, lat, lon) in enumerate(nodes, start=1):
            nodo = origin.relational_nodos.create(
                name=name,
                lat=str(lat),
                lon=str(lon),
                quadrant="",
            )
            DispatchStop.objects.create(
                batch=dispatch_batch,
                nodo=nodo,
                address=name,
                lat=str(lat),
                lon=str(lon),
            )
        return origin

    def _route_destinations(self, origin):
        return [
            route.json_dic()["Destinos"][0]
            for route in origin.relational_route.order_by("sequence_number", "id")
        ]

    def test_create_route_balances_group_sizes_when_possible(self):
        origin = self._create_origin_with_nodes(
            [
                ("A", -12.0500, -77.0400),
                ("B", -12.0510, -77.0390),
                ("C", -12.0520, -77.0380),
                ("D", -12.0800, -77.0100),
                ("E", -12.0810, -77.0110),
                ("F", -12.0790, -77.0120),
            ]
        )

        origin.define_all_routes()

        route_sizes = [len(destinations) for destinations in self._route_destinations(origin)]
        self.assertEqual(route_sizes, [3, 3])

    def test_create_route_keeps_clusters_together_for_simple_two_cluster_case(self):
        origin = self._create_origin_with_nodes(
            [
                ("A", -12.0500, -77.0400),
                ("B", -12.0510, -77.0390),
                ("C", -12.0520, -77.0380),
                ("D", -12.0800, -77.0100),
                ("E", -12.0810, -77.0110),
                ("F", -12.0790, -77.0120),
            ]
        )
        self.organization.max_stops_per_route = 3
        self.organization.save(update_fields=["max_stops_per_route"])

        origin.define_all_routes()

        routes = [set(destinations) for destinations in self._route_destinations(origin)]
        expected_clusters = [{"A", "B", "C"}, {"D", "E", "F"}]
        self.assertCountEqual(routes, expected_clusters)

    def test_create_route_updates_dispatch_batch_version_and_assigns_stops(self):
        origin = self._create_origin_with_nodes(
            [
                ("A", -12.0500, -77.0400),
                ("B", -12.0510, -77.0390),
                ("C", -12.0520, -77.0380),
            ]
        )

        first_route = origin.define_all_routes()
        origin.dispatch_batch.refresh_from_db()

        self.assertIsNotNone(first_route)
        self.assertEqual(origin.dispatch_batch.algorithm_version, "heuristic-sweep-v3")
        self.assertEqual(origin.dispatch_batch.status, DispatchBatch.Statuses.GENERATED)
        self.assertEqual(
            origin.dispatch_batch.stops.filter(route__isnull=False).count(),
            3,
        )
