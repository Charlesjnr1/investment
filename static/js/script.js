// Function to fetch cryptocurrency data from CoinRanking API
async function fetchCryptoData() {
	try {
		const response = await
			fetch('https://api.coinranking.com/v2/coins');
		const data = await response.json();
		return data.data.coins;
	} catch (error) {
		console.error('Error fetching cryptocurrency data:', error);
		return [];
	}
}

// Function to display cryptocurrency data in the table
function displayCryptoData(coins) {
	const cryptoTable = document.getElementById('cryptoTable');
	cryptoTable.innerHTML = '';

	coins.forEach(coin => {
		const row = document.createElement('tr');
		row.innerHTML = `
		<td><img src="${coin.iconUrl}"
		class="crypto-logo" alt="${coin.name}"></td>
			<td>${coin.name}</td>
			<td>${coin.symbol}</td>
			<td>$${coin.price}</td>
			<td>${coin.change}%</td>
			<td>${coin.volume ? coin.volume : '-'}</td>
			<td>${coin.marketCap ? coin.marketCap : '-'}</td>
		`;
		cryptoTable.appendChild(row);
	});
}

// Function to filter cryptocurrencies based on user input
function filterCryptoData(coins, searchTerm) {
	searchTerm = searchTerm.toLowerCase();

	const filteredCoins = coins.filter(coin =>
		coin.name.toLowerCase().includes(searchTerm) ||
		coin.symbol.toLowerCase().includes(searchTerm)
	);

	return filteredCoins;
}

// Function to handle search input
function handleSearchInput() {
	const searchInput = document.getElementById('searchInput');
	const searchTerm = searchInput.value.trim();

	fetchCryptoData().then(coins => {
		const filteredCoins = filterCryptoData(coins,
			searchTerm);
		displayCryptoData(filteredCoins);
	});
}

// Function to initialize the app
async function initializeApp() {
	const coins = await fetchCryptoData();
	displayCryptoData(coins);

	// Add event listener to search input
	const searchInput = 
		document.getElementById('searchInput');
	searchInput.addEventListener('input',
		handleSearchInput);
}

// Call initializeApp function
// when the DOM content is loaded
const coinList = [
	"bitcoin", "ethereum", "solana", "cardano", "dogecoin",
	"binancecoin", "ripple", "tron", "polkadot", "litecoin",
	"avalanche-2", "chainlink", "shiba-inu", "uniswap", "cosmos",
	"stellar", "vechain", "aptos", "the-graph", "algorand"
  ];
  
  async function loadCryptoTicker() {
	try {
	  const priceRes = await fetch(
		`https://api.coingecko.com/api/v3/simple/price?ids=${coinList.join(',')}&vs_currencies=usd`
	  );
	  const prices = await priceRes.json();
  
	  const coinRes = await fetch(
		`https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=${coinList.join(',')}`
	  );
	  const coins = await coinRes.json();
  
	  const ticker = document.querySelector('.ticker');
	  const clone = document.querySelector('.ticker.clone');
	  ticker.innerHTML = '';
	  clone.innerHTML = '';
  
	  let html = '';
  
	  coins.forEach(coin => {
		const price = prices[coin.id]?.usd;
		if (price !== undefined) {
		  html += `
			<span>
			  <img src="${coin.image}" alt="${coin.symbol}">
			  ${coin.name}: $${price.toLocaleString()}
			</span>
		  `;
		}
	  });
  
	  ticker.innerHTML = html;
	  clone.innerHTML = html; // duplicate for seamless scroll
	} catch (err) {
	  console.error('Error loading crypto data:', err);
	  document.querySelector('.ticker').innerHTML = 'Unable to load prices.';
	}
  }
  
  loadCryptoTicker();
  setInterval(loadCryptoTicker, 90000); // refresh every 60s