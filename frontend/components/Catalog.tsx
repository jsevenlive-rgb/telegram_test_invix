"use client";

import { useEffect, useState } from "react";
import { fetchCatalog, type ProductFeedItem } from "@/lib/api";
import { ProductCard } from "./ProductCard";

export function Catalog() {
  const [items, setItems] = useState<ProductFeedItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCatalog({ cache: "no-store" })
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <div className="error">Не удалось загрузить каталог: {error}</div>;
  }

  if (items === null) {
    return <div className="loading">Загрузка каталога…</div>;
  }

  if (items.length === 0) {
    return (
      <div className="empty">
        Пока нет товаров.
        <br />
        Создай магазин в боте и размести первый товар.
      </div>
    );
  }

  return (
    <div className="grid">
      {items.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}
