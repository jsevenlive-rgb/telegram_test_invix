import { Catalog } from "@/components/Catalog";

export default function CatalogPage() {
  return (
    <main className="page">
      <header className="header">
        <h1>Каталог</h1>
        <p>Публичная лента товаров из всех магазинов</p>
        <span className="badge">Telegram Mini App · браузер</span>
      </header>
      <Catalog />
    </main>
  );
}
