export function load() {
	const today = new Date();
	const options = {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
		weekday: 'long'
	  };
	const formattedDate = today.toLocaleDateString('en-US', options);

	return {
		today: formattedDate
	};
}
