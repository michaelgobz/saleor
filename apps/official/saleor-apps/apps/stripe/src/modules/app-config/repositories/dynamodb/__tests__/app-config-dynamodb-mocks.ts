import {
  mockedConfigurationId,
  mockedSaleorAppId,
  mockedSaleorChannelId,
} from "@/__tests__/mocks/constants";
import { mockEncryptor } from "@/__tests__/mocks/mock-encryptor";
import { mockedSaleorApiUrl } from "@/__tests__/mocks/saleor-api-url";

const mockedStripeConfig = {
  configName: "tasdafsdf",
  createdAt: "2025-04-25T09:19:13.402Z",
  stripeWhId: "we_1RHiPdKFxIUko8m01KAnXiRQ",
  configId: mockedConfigurationId,
  stripePk: "pk_test_fixture",
  modifiedAt: "2025-04-25T09:19:13.402Z",
  stripeWhSecret: mockEncryptor.encrypt("whsec_fixture"),
  SK: `CONFIG_ID#${mockedConfigurationId}`,
  stripeRk: mockEncryptor.encrypt(
    "rk_test_fixture",
  ),
  PK: `${mockedSaleorApiUrl}#${mockedSaleorAppId}`,
  _et: "StripeConfig",
};

const mockedMapping = {
  createdAt: "2025-04-25T10:26:30.219Z",
  configId: mockedConfigurationId,
  modifiedAt: "2025-04-25T10:26:30.219Z",
  SK: `CHANNEL_ID#${mockedSaleorChannelId}`,
  PK: `${mockedSaleorApiUrl}#${mockedSaleorAppId}`,
  channelId: mockedSaleorChannelId,
  _et: "ChannelConfigMapping",
};

export const mockedDynamoConfigItems = {
  mockedStripeConfig,
  mockedMapping,
};
