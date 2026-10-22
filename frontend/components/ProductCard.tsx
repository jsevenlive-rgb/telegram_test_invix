import { formatPrice, type ProductFeedItem } from "@/lib/api";

export function ProductCard({ product }: { product: ProductFeedItem }) {
  const price = formatPrice(product.price);

  return (
    <article className="card">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className="card-image"
        src={product.image_url}
        alt={product.title}
        loading="lazy"
      />
      <div className="card-body">
        <div className="card-shop">{product.shop_name}</div>
        <h2 className="card-title">{product.title}</h2>
        {price && <div className="card-price">{price}</div>}
      </div>
    </article>
  );
}
