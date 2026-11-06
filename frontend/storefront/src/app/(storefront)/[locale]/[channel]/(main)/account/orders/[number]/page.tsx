import { Suspense } from "react";
import { notFound } from "next/navigation";
import Image from "next/image";
import { MapPin, CreditCard } from "lucide-react";
import { getTranslations } from "next-intl/server";
import { getOrdersForNumberLookup } from "@/lib/account/get-orders";
import { hasAuthSession } from "@/lib/auth/has-auth-session";
import { resolveLocaleFromSlug } from "@/config/locale";
import { pickTranslatedName } from "@/lib/saleor-translations";
import { LinkWithChannel } from "@/ui/atoms/link-with-channel";
import { formatDate, formatMoney } from "@/lib/utils";
import { OrderTimeline } from "@/ui/components/account/order-timeline";
import { OrderStatusBadge } from "@/ui/components/account/order-status-badge";
import { AccountOrderDetailSkeleton } from "@/ui/components/account/account-skeleton";
import { type AddressDetailsFragment } from "@/gql/graphql";

type Props = {
	params: Promise<{ locale: string; number: string }>;
};

export default function OrderDetailPage({ params }: Props) {
	return (
		<Suspense fallback={<AccountOrderDetailSkeleton />}>
			<OrderDetailContent params={params} />
		</Suspense>
	);
}

async function OrderDetailContent({ params }: Props) {
	const { number, locale } = await params;
	const intlLocale = resolveLocaleFromSlug(locale).bcp47;
	const t = await getTranslations({ locale, namespace: "account.orderDetail" });
	const tCommon = await getTranslations({ locale, namespace: "account.common" });
	const tOrders = await getTranslations({ locale, namespace: "account.orders" });

	if (!(await hasAuthSession())) {
		return <p className="text-sm text-muted-foreground">{t("signInRequired")}</p>;
	}

	const result = await getOrdersForNumberLookup(locale);

	if (!result.ok) {
		return <p className="text-sm text-muted-foreground">{t("loadFailed")}</p>;
	}

	if (!result.data.me) {
		return <p className="text-sm text-muted-foreground">{t("signInRequired")}</p>;
	}

	const orders = result.data.me.orders?.edges ?? [];
	const order = orders.find(({ node }) => node.number === number)?.node;

	if (!order) {
		notFound();
	}

	const itemCount = order.lines.reduce((sum, l) => sum + l.quantity, 0);
	const placedDate = formatDate(new Date(order.created), undefined, intlLocale);

	return (
		<div className="space-y-6">
			<div className="flex flex-wrap items-start justify-between gap-4">
				<div>
					<h1 className="text-balance text-h1">{tOrders("orderNumber", { number: order.number })}</h1>
					<p className="mt-1 text-sm text-muted-foreground">{t("placedOn", { date: placedDate })}</p>
				</div>
				<OrderStatusBadge status={order.status} statusDisplay={order.statusDisplay} localeSlug={locale} />
			</div>

			<div className="grid gap-6 lg:grid-cols-[1fr_320px]">
				<div className="space-y-6">
					<div className="rounded-xl border">
						<div className="border-b px-5 py-4">
							<h2 className="text-sm font-semibold">{t("items", { count: itemCount })}</h2>
						</div>
						<div className="divide-y">
							{order.lines.map((line) => {
								if (!line.variant) return null;
								const variant = line.variant;
								const product = variant.product;
								const productName = pickTranslatedName(product);
								const variantName = pickTranslatedName(variant);
								const lineTotal = variant.pricing?.price?.gross
									? variant.pricing.price.gross.amount * line.quantity
									: null;
								const currency = variant.pricing?.price?.gross.currency;
								return (
									<div key={line.id} className="flex items-center gap-4 px-5 py-4">
										{product.thumbnail && (
											<div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg border bg-secondary/30">
												<Image
													src={product.thumbnail.url}
													alt={product.thumbnail.alt ?? productName}
													width={128}
													height={128}
													className="h-full w-full object-contain"
												/>
											</div>
										)}
										<div className="min-w-0 flex-1">
											<LinkWithChannel
												href={`/products/${product.slug}`}
												className="text-sm font-medium hover:underline"
											>
												{productName}
											</LinkWithChannel>
											{variantName !== variant.id && Boolean(variantName) && (
												<p className="text-[13px] text-muted-foreground">{variantName}</p>
											)}
											<p className="text-[13px] text-muted-foreground">
												{tCommon("qty", { count: line.quantity })}
											</p>
										</div>
										{lineTotal != null && currency && (
											<span className="text-sm font-medium tabular-nums">
												{formatMoney(lineTotal, currency, intlLocale)}
											</span>
										)}
									</div>
								);
							})}
						</div>

						<div className="border-t px-5 py-4">
							<dl className="space-y-2 text-sm">
								<div className="flex justify-between">
									<dt className="text-muted-foreground">{t("subtotal")}</dt>
									<dd className="tabular-nums">
										{formatMoney(order.subtotal.gross.amount, order.subtotal.gross.currency, intlLocale)}
									</dd>
								</div>
								<div className="flex justify-between">
									<dt className="text-muted-foreground">{t("shipping")}</dt>
									<dd className="tabular-nums">
										{order.shippingPrice.gross.amount === 0
											? tCommon("free")
											: formatMoney(
													order.shippingPrice.gross.amount,
													order.shippingPrice.gross.currency,
													intlLocale,
												)}
									</dd>
								</div>
								{order.total.tax.amount > 0 && (
									<div className="flex justify-between">
										<dt className="text-muted-foreground">{t("tax")}</dt>
										<dd className="tabular-nums">
											{formatMoney(order.total.tax.amount, order.total.tax.currency, intlLocale)}
										</dd>
									</div>
								)}
								<div className="flex justify-between border-t pt-2 font-semibold">
									<dt>{t("total")}</dt>
									<dd className="tabular-nums">
										{formatMoney(order.total.gross.amount, order.total.gross.currency, intlLocale)}
									</dd>
								</div>
							</dl>
						</div>
					</div>

					<OrderTimeline order={order} localeSlug={locale} />
					<OrderTrackingPanel fulfillments={order.fulfillments} />
				</div>

				<div className="space-y-4">
					{order.shippingAddress && (
						<OrderAddress title={t("shippingAddress")} address={order.shippingAddress} />
					)}
					{order.billingAddress && (
						<OrderAddress title={t("billingAddress")} address={order.billingAddress} />
					)}

					{order.isPaid && (
						<div className="rounded-xl border px-5 py-4">
							<h3 className="mb-3 text-sm font-semibold">{t("paymentMethod")}</h3>
							<div className="flex items-center gap-3">
								<CreditCard className="h-4 w-4 text-muted-foreground" />
								<span className="text-sm">
									{order.paymentStatus === "FULLY_CHARGED" ? t("paid") : order.paymentStatus}
								</span>
							</div>
						</div>
					)}

					<LinkWithChannel
						href="/contact"
						className="block w-full rounded-xl border px-5 py-3 text-center text-sm font-medium transition-colors hover:bg-secondary/50"
					>
						{t("needHelp")}
					</LinkWithChannel>
				</div>
			</div>
		</div>
	);
}

function OrderTrackingPanel({
	fulfillments,
}: {
	fulfillments: Array<{
		id: string;
		status: string;
		trackingNumber: string;
		shipment?: {
			id: string;
			carrier: string;
			status: string;
			trackingNumber: string;
			latestLocation?: {
				latitude: number;
				longitude: number;
				accuracyMeters?: number | null;
				capturedAt: string;
			} | null;
		} | null;
	}>;
}) {
	const trackedFulfillments = fulfillments.filter((fulfillment) => fulfillment.shipment);

	if (trackedFulfillments.length === 0) {
		return null;
	}

	return (
		<div className="rounded-xl border px-5 py-4">
			<div className="flex items-start justify-between gap-4">
				<div>
					<h2 className="text-sm font-semibold">Delivery tracking</h2>
					<p className="mt-1 text-[13px] text-muted-foreground">
						Latest location reported by the delivery partner.
					</p>
				</div>
				<MapPin className="h-4 w-4 text-muted-foreground" />
			</div>

			<div className="mt-4 space-y-4">
				{trackedFulfillments.map((fulfillment) => {
					const shipment = fulfillment.shipment!;
					const location = shipment.latestLocation;

					return (
						<div key={fulfillment.id} className="rounded-lg bg-secondary/30 p-4">
							<div className="flex flex-wrap items-center justify-between gap-2 text-sm">
								<span className="font-medium">{shipment.carrier}</span>
								<span className="text-muted-foreground">{shipment.status}</span>
							</div>
							<p className="mt-1 text-[13px] text-muted-foreground">
								{shipment.trackingNumber || fulfillment.trackingNumber || "Tracking number pending"}
							</p>
							{location ? (
								<div className="relative mt-3 h-32 overflow-hidden rounded-md border bg-[linear-gradient(135deg,#eef5f1_25%,transparent_25%)] bg-[length:24px_24px]">
									<div
										className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-blue-600 shadow"
										style={{
											left: `${((location.longitude + 180) / 360) * 100}%`,
											top: `${((90 - location.latitude) / 180) * 100}%`,
										}}
									/>
									<div className="absolute bottom-2 left-2 rounded bg-background/90 px-2 py-1 text-[11px] text-muted-foreground">
										{location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
									</div>
								</div>
							) : (
								<p className="mt-3 text-[13px] text-muted-foreground">
									Waiting for the first GPS update.
								</p>
							)}
						</div>
					);
				})}
			</div>
		</div>
	);
}

function OrderAddress({ title, address }: { title: string; address: AddressDetailsFragment }) {
	return (
		<div className="rounded-xl border px-5 py-4">
			<h3 className="mb-3 text-sm font-semibold">{title}</h3>
			<div className="flex gap-3">
				<MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
				<div className="text-sm leading-relaxed">
					<p className="font-medium">
						{address.firstName} {address.lastName}
					</p>
					<p className="text-muted-foreground">{address.streetAddress1}</p>
					{address.streetAddress2 && <p className="text-muted-foreground">{address.streetAddress2}</p>}
					<p className="text-muted-foreground">
						{address.postalCode} {address.city}
					</p>
					<p className="text-muted-foreground">{address.country.country}</p>
				</div>
			</div>
		</div>
	);
}
