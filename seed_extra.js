const { MongoClient } = require('mongodb');
const uri = 'mongodb://localhost:27017';
const client = new MongoClient(uri);

async function run() {
    try {
        await client.connect();
        const db = client.db('rigmaster');
        const components = db.collection('components');

        const newComponents = [
            { name: 'Samsung Odyssey G7 27"', category: 'monitor', brand: 'Samsung', status: 'Active', price: 549, specs: '1440p, 240Hz' },
            { name: 'LG UltraGear 27GP850-B', category: 'monitor', brand: 'LG', status: 'Active', price: 349, specs: '1440p, 165Hz' },
            { name: 'ASUS ROG Swift PG279QM', category: 'monitor', brand: 'ASUS', status: 'Active', price: 699, specs: '1440p, 240Hz' },
            { name: 'Windows 11 Home', category: 'os', brand: 'Microsoft', status: 'Active', price: 109, specs: '64-bit' },
            { name: 'Windows 11 Pro', category: 'os', brand: 'Microsoft', status: 'Active', price: 149, specs: '64-bit' },
            { name: 'Linux Mint 21', category: 'os', brand: 'Mint', status: 'Active', price: 0, specs: 'Free' },
            { name: 'Logitech G Pro X Superlight', category: 'peripherals', brand: 'Logitech', status: 'Active', price: 129, specs: 'Wireless Mouse' },
            { name: 'Razer Huntsman V2', category: 'peripherals', brand: 'Razer', status: 'Active', price: 159, specs: 'Mechanical Keyboard' },
            { name: 'Corsair LL120 RGB 3-Pack', category: 'fans', brand: 'Corsair', status: 'Active', price: 99, specs: '120mm PWM Fans' },
            { name: 'Be Quiet! Silent Wings 4 120mm', category: 'fans', brand: 'Be Quiet!', status: 'Active', price: 29, specs: 'Quiet Fan' }
        ];

        const result = await components.insertMany(newComponents);
        console.log(`${result.insertedCount} components inserted.`);
    } finally {
        await client.close();
    }
}
run().catch(console.dir);
