import { createStripeRestrictedKey } from "@/modules/stripe/stripe-restricted-key";

export const mockedStripeRestrictedKey = createStripeRestrictedKey(
  "rk_live_fixture",
)._unsafeUnwrap();

export const mockedStripeRestrictedKeyTest = createStripeRestrictedKey(
  "rk_test_fixture",
)._unsafeUnwrap();
