import './globals.css';

export const metadata = {
  title: 'Ontology News Engine',
  description: 'AI-powered LinkedIn content generator driven by behavioral science.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased bg-black text-white min-h-screen">
        {children}
      </body>
    </html>
  );
}