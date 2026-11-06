import { useQuery } from "@apollo/client";
import { Box, Text } from "@saleor/macaw-ui-next";
import { useMemo } from "react";

import { logisticsOverviewQuery } from "./queries";

type Location = {
  latitude: number;
  longitude: number;
  accuracyMeters?: number | null;
  capturedAt: string;
};

type Shipment = {
  id: string;
  carrier: string;
  status: string;
  trackingNumber: string;
  latestLocation?: Location | null;
};

type LogisticsOverviewData = {
  orders: {
    edges: Array<{
      node: {
        id: string;
        number: string;
        fulfillments: Array<{
          id: string;
          status: string;
          trackingNumber: string;
          shipment?: Shipment | null;
        }>;
      };
    }>;
  };
};

const cardStyle = {
  border: "1px solid #e3e5e8",
  borderRadius: 8,
  padding: 20,
  background: "#fff",
};

export default function LogisticsPage() {
  const { data, loading, error } = useQuery<LogisticsOverviewData>(logisticsOverviewQuery, {
    pollInterval: 30000,
  });
  const shipments = useMemo(
    () =>
      data?.orders.edges.flatMap(edge =>
        edge.node.fulfillments
          .filter(fulfillment => fulfillment.shipment)
          .map(fulfillment => ({
            orderNumber: edge.node.number,
            shipment: fulfillment.shipment!,
          })),
      ) ?? [],
    [data],
  );
  const activeLocations = shipments
    .map(item => item.shipment.latestLocation)
    .filter((location): location is Location => Boolean(location));

  return (
    <Box padding={6} display="flex" flexDirection="column" gap={6}>
      <Box>
        <Text as="h1" size={7} fontWeight="bold">
          Logistics & accounting
        </Text>
        <Text color="default2">
          Monitor delivery operations and the GPS position reported by delivery devices.
        </Text>
      </Box>

      {error && <Text color="critical1">Unable to load logistics data: {error.message}</Text>}

      <Box display="grid" __gridTemplateColumns="minmax(0, 2fr) minmax(280px, 1fr)" gap={6}>
        <div style={cardStyle}>
          <Text as="h2" size={5} fontWeight="bold">
            Live delivery map
          </Text>
          <Text color="default2">
            {loading ? "Loading shipment locations…" : `${activeLocations.length} active GPS locations`}
          </Text>
          <div
            style={{
              position: "relative",
              height: 360,
              marginTop: 16,
              overflow: "hidden",
              borderRadius: 8,
              background:
                "linear-gradient(135deg, #eef5f1 25%, transparent 25%) -20px 0/40px 40px, linear-gradient(225deg, #eef5f1 25%, transparent 25%) -20px 0/40px 40px, linear-gradient(315deg, #eef5f1 25%, transparent 25%) 0 0/40px 40px, linear-gradient(45deg, #eef5f1 25%, #f8faf9 25%) 0 0/40px 40px",
            }}
          >
            {activeLocations.map((location, index) => (
              <span
                key={`${location.capturedAt}-${index}`}
                title={`${location.latitude}, ${location.longitude}`}
                style={{
                  position: "absolute",
                  left: `${((location.longitude + 180) / 360) * 100}%`,
                  top: `${((90 - location.latitude) / 180) * 100}%`,
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  background: "#1976d2",
                  border: "3px solid #fff",
                  boxShadow: "0 1px 5px rgba(0,0,0,.3)",
                  transform: "translate(-50%, -50%)",
                }}
              />
            ))}
            {activeLocations.length === 0 && (
              <Text color="default2" textAlign="center" style={{ display: "block", paddingTop: 160 }}>
                No GPS samples have been reported yet.
              </Text>
            )}
          </div>
        </div>

        <div style={cardStyle}>
          <Text as="h2" size={5} fontWeight="bold">
            Shipment activity
          </Text>
          <Text color="default2">{shipments.length} linked shipments</Text>
          <Box display="flex" flexDirection="column" gap={3} marginTop={4}>
            {shipments.slice(0, 8).map(({ orderNumber, shipment }) => (
              <Box key={shipment.id} display="flex" justifyContent="space-between" gap={3}>
                <Box>
                  <Text fontWeight="bold">Order {orderNumber}</Text>
                  <Text size={2} color="default2">
                    {shipment.carrier} · {shipment.trackingNumber || "No tracking number"}
                  </Text>
                </Box>
                <Text size={2}>{shipment.status}</Text>
              </Box>
            ))}
            {!loading && shipments.length === 0 && <Text color="default2">No logistics shipments found.</Text>}
          </Box>
        </div>
      </Box>

      <div style={cardStyle}>
        <Text as="h2" size={5} fontWeight="bold">
          Accounting workspace
        </Text>
        <Text color="default2">
          Expected inventory cost and journal export are handled by the accounting adapter. Connect the
          adapter in Saleor settings to enable reconciliation and ERP export workflows.
        </Text>
      </div>
    </Box>
  );
}
