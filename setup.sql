drop table if exists user_coupon_usage;

drop table if exists coupons;
create table coupons (
  id serial primary key,
  code varchar(64) unique not null,
  amount integer default 0 check (amount>=0)
);
create index on coupons(code);
insert into coupons (code, amount) values (md5(random()::text || clock_timestamp()::text)::uuid, 10000);

drop table if exists users;
create table users (
  id serial primary key
);
insert into users select * from generate_series(1, 100000);

create table user_coupon_usage (
  coupon_id integer,
  user_id integer,
  primary key(coupon_id, user_id),
  foreign key (coupon_id) references coupons(id),
  foreign key (user_id) references users(id)
);
