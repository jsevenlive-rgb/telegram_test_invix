export type ProductFeedItem = {
  id: number;
  shop_id: number;
  shop_name: string;
  title: string;
  description: string | null;
  price: string | number | null;
  image_url: string;
  created_at: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function fetchCatalog(
  init?: RequestInit
): Promise<ProductFeedItem[]> {
  const res = await fetch(`${API_URL}/api/products?limit=100`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
    next: { revalidate: 15 },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export function formatPrice(price: string | number | null): string | null {
  if (price === null || price === undefined || price === "") return null;
  const n = typeof price === "number" ? price : Number(price);
  if (Number.isNaN(n)) return String(price);
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);
}
