-- Test data (fictional students, hashes are placeholders)

INSERT INTO categories (name) VALUES
 ('Books'), ('Electronics'), ('Clothes'), ('Dorm items'), ('Services');

INSERT INTO users (student_id, full_name, email, password_hash, phone) VALUES
 ('24B000101', 'Aruzhan Seitkali',  'aruzhan@kbtu.kz',  'hash_1', '+77010000001'),
 ('24B000102', 'Dias Omarov',       'dias@kbtu.kz',     'hash_2', '+77010000002'),
 ('24B000103', 'Madina Kassym',     'madina@kbtu.kz',   'hash_3', '+77010000003'),
 ('24B000104', 'Timur Akhmetov',    'timur@kbtu.kz',    'hash_4', '+77010000004'),
 ('24B000105', 'Aigerim Zhunus',    'aigerim@kbtu.kz',  'hash_5', '+77010000005'),
 ('24B000106', 'Nursultan Bek',     'nursultan@kbtu.kz','hash_6', NULL),
 ('24B000107', 'Kamila Serik',      'kamila@kbtu.kz',   'hash_7', '+77010000007'),
 ('24B000108', 'Yerlan Tokhtar',    'yerlan@kbtu.kz',   'hash_8', NULL),
 ('24B000109', 'Dana Ibrayeva',     'dana@kbtu.kz',     'hash_9', '+77010000009'),
 ('24B000110', 'Arman Mukhtar',     'arman@kbtu.kz',    'hash_10','+77010000010');

INSERT INTO listings (seller_id, category_id, title, description, price, condition, status) VALUES
 (1, 1, 'Calculus textbook, Stewart 8th ed', 'Some notes in pencil', 4500, 'used', 'active'),
 (1, 1, 'Discrete Math lecture notes',       'Handwritten, full semester', 2000, 'used', 'active'),
 (2, 2, 'Logitech wireless mouse',           'Works perfectly', 3500, 'used', 'active'),
 (2, 2, 'USB-C charger 65W',                 'Original box', 9000, 'new', 'sold'),
 (3, 3, 'University hoodie, size M',         'Worn twice', 6000, 'used', 'active'),
 (3, 4, 'Desk lamp',                         'LED, 3 brightness levels', 4000, 'used', 'active'),
 (4, 1, 'Intro to Databases, Elmasri',       'Like new', 7000, 'used', 'active'),
 (4, 2, 'Mechanical keyboard',               'Blue switches', 15000, 'used', 'active'),
 (5, 4, 'Electric kettle',                   '1.7 L', 5000, 'used', 'sold'),
 (5, 5, 'Python tutoring, 1 hour',           'Beginner level', 3000, 'new', 'active'),
 (6, 1, 'English B2 workbook',               'Not filled in', 3000, 'new', 'active'),
 (6, 3, 'Winter jacket, size L',             'Warm, black', 18000, 'used', 'active'),
 (7, 2, 'Headphones Sony WH-CH520',          '6 months old', 14000, 'used', 'active'),
 (7, 4, 'Bedsheet set',                      'Single bed', 4500, 'new', 'active'),
 (8, 5, 'Essay proofreading',                'English, per page', 1000, 'new', 'active'),
 (8, 1, 'Physics 1 problem book',            'Solutions included', 2500, 'used', 'hidden'),
 (9, 2, 'Graphing calculator Casio',         'With batteries', 12000, 'used', 'active'),
 (9, 3, 'Sneakers, size 38',                 'Barely used', 9000, 'used', 'active'),
 (10, 4, 'Mini fridge',                      'For dorm room', 25000, 'used', 'active'),
 (10, 1, 'Statistics textbook',              'Good condition', 4000, 'used', 'active');

INSERT INTO messages (listing_id, sender_id, receiver_id, text) VALUES
 (1, 3, 1, 'Hi! Is the Calculus book still available?'),
 (1, 1, 3, 'Yes, you can pick it up tomorrow at the library.'),
 (8, 2, 4, 'Would you sell the keyboard for 13000?'),
 (8, 4, 2, 'OK, deal.'),
 (13, 5, 7, 'Do the headphones have any scratches?'),
 (19, 6, 10, 'Can you deliver the fridge to dorm 2?');

INSERT INTO favourites (user_id, listing_id) VALUES
 (1, 3),
 (1, 5),
 (2, 3);
