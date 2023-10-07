The challenge presents us with a simple page with 16-bit graphics containing a vending machine that sells various products. We have one coupon available, worth 1 dollar, that we can insert in the machine to redeem and be able to buy stuff.


```
web_diogenes_rage/
├── Dockerfile
├── build-docker.sh
├── challenge
│   ├── database.js
│   ├── flag
│   ├── helpers
│   │   └── JWTHelper.js
│   ├── index.js
│   ├── middleware
│   │   └── AuthMiddleware.js
│   ├── package.json
│   ├── routes
│   │   └── index.js
│   ├── static
│   │   ├── css
│   │   │   ├── bootstrap.min.css
│   │   │   └── main.css
│   │   ├── images
│   │   │   ├── bat.gif
│   │   │   ├── brickwall.png
│   │   │   ├── clam-chowder.png
│   │   │   ├── coupon.png
│   │   │   ├── favicon.png
│   │   │   ├── film-reel.png
│   │   │   ├── ikea-catalog.png
│   │   │   ├── marlboro.png
│   │   │   ├── meow.gif
│   │   │   ├── motor-oil.png
│   │   │   ├── pavement.png
│   │   │   ├── rayhan.gif
│   │   │   ├── road.png
│   │   │   ├── sky.jpg
│   │   │   ├── soap.png
│   │   │   ├── starbucks.png
│   │   │   ├── vet-medicine.png
│   │   │   └── vinegar.png
│   │   └── js
│   │       ├── jquery-3.6.0.min.js
│   │       ├── jquery-ui.js
│   │       ├── jquery.marquee.min.js
│   │       └── main.js
│   └── views
│       └── index.html
└── config
    └── supervisord.conf
```

It's a Node.js application.

From `routes/index.js` we can see that it exposes API endpoints to purchase items, redeem coupons and reset the session.

If we try to redeem our coupon or buy an item and we intercept the requests, we indeed see POST requests being made to those endpoints, with a JSON body.

Looking at the `/api/purchase` endpoint, we notice that we can obtain the flag by purchasing the 'C8' product. The problem is that it costs 13.37 dollars and our coupon is only worth 1 dollar.

The app uses JWTs to keep track of the session and the session cookie is set the first time we make a request to either `/api/purchase` or `/api/coupons/apply`.
The JWT seems to be handled properly: the algorithm is hardcoded and the secret used to sign it is too long to be bruteforced. Plus, no previous user is present in the database so, even if we could forge session cookies, that wouldn't really be of any use.

The only way to proceed seems to be finding a way to increase the amount of money that the coupon gives on redemption.
We cannot forge new coupons with arbitrary values since a coupon is checked against a list of legit coupons in the database, and the `HTB_100` coupon is the only one in the db.

If we take a look at the code in `/api/coupons/apply` we can see that it first checks whether a coupon has already been redeemed by looking at the column `coupons` column in the user db entry.
If the coupon has not been redeemed yet, it **first** adds the coupon value to the user's balance and **then** sets the coupon as used.
There is a time frame during which the user's balance has been increased but the coupon has not been redeemed yet.
We can exploit this race condition to send a bunch of copies of the same coupon in a short time hoping that they will all be redeemed before the first one is set as redeemed.

```javascript
			if (coupon_code) {
				if (user.coupons.includes(coupon_code)) {
					return res.status(401).send(response("This coupon is already redeemed!"));
				}
				return db.getCouponValue(coupon_code)
					.then(coupon => {
						if (coupon) {
							return db.addBalance(user.username, coupon.value)
								.then(() => {
									db.setCoupon(user.username, coupon_code)
										.then(() => res.send(response(`$${coupon.value} coupon redeemed successfully! Please select an item for order.`)))
								})
								.catch(() => res.send(response("Failed to redeem the coupon!")));
						}
						res.send(response("No such coupon exists!"));
					})
			}
```

The attack plan is to first obtain a session cookie, and we can do so by trying to purchase any item without having any balance in our account.
Then, using this session cookie, we send a bunch of redeem requests with `{"coupon_code":"HTB_100"}` .
Finally, we can purchase the product C8 and get our flag.

I tried to script this with Python but it was too slow, so I resorted to an extension of Burp Suite called "Turbo repeater" which allows to send quick bursts of requests using parallel connections.

The implementation of the attack is left as an exercise to the reader :)