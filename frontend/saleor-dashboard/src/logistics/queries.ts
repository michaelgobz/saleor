import { gql } from "@apollo/client";

export const logisticsOverviewQuery = gql`
  query LogisticsOverview {
    orders(first: 50, sortBy: { field: CREATED_AT, direction: DESC }) {
      edges {
        node {
          id
          number
          fulfillments {
            id
            status
            trackingNumber
            shipment {
              id
              carrier
              status
              trackingNumber
              latestLocation {
                id
                latitude
                longitude
                accuracyMeters
                capturedAt
              }
            }
          }
        }
      }
    }
  }
`;
