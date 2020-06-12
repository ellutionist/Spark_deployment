import psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
import sys
import os
import numpy as np


def pgconnect(user, psw, host, database, port):
    try:
        conn = psycopg2.connect(host=host,
                                database=database,
                                user=user,
                                password=psw,
                                port=port,
                                connect_timeout=3)
        print('connected')
        return conn
    except Exception as e:
        print('connect failed')
        return None


def pgquery(conn, sqlcmd, args=None, silent=False):
    retval = None
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        try:
            if args is None:
                cur.execute(sqlcmd)
            else:
                cur.execute(sqlcmd, args)
            retval = cur.fetchall()
        except Exception as e:
            if not silent:
                print('db read error:')
                print(e)
                print(sqlcmd)
        cur.execute('commit;')
    return retval


def main(app_id: int, num_points_per_period: int):
    conn = pgconnect("ellutionist", "p1995620c", "localhost", "ellutionist", 5433)

    kwargs = {"app_id": app_id}

    result = pgquery(conn, "SELECT * FROM latency WHERE id=%(app_id)s ORDER BY time ASC", kwargs)

    # The first period is to stable the connection, which has no meaning.
    result = result[num_points_per_period:]

    latencies = []
    nums_record = []
    for row in result:
        latencies.append(row["delay"])
        nums_record.append(row["num_records"] / 1000)

    i = 0
    means = []
    n_points = len(latencies)
    while n_points - i * num_points_per_period >= 10:
        n_points_left_in_period = min(30, n_points - i * num_points_per_period)
        mean = np.mean(latencies[i * 30:i * 30 + n_points_left_in_period])
        for j in range(n_points_left_in_period):
            means.append(mean)
        i = i + 1

    plt.figure(figsize=(16, 8))
    plt.xticks(range(0, 2 * len(latencies), 10))

    tick = max(int(max(latencies)/20/100)*100, 100)
    plt.yticks(range(0, 20000, tick))
    plt.xlabel("Second", fontsize=20)
    plt.ylabel("Delay (ms)", fontsize=20)
    plt.plot(range(0, 2 * len(latencies), 2), latencies, color="r", label="Real-time Delay")
    plt.plot(range(2, 2 * len(means) + 2, 2), means, color="navy", label="Average Delay", linestyle="--")
    plt.legend(fontsize=15)

    height_shift = max(latencies) / 20
    for k in range(int(len(means) / num_points_per_period)):
        idx = k * num_points_per_period
        plt.text(idx * 2 + num_points_per_period, means[idx] + height_shift, '%.2f' % means[idx], ha='center', va='top',
                 fontsize=18, color="navy")

    if max(latencies) >= 2000:
        plt.hlines(2000, 0, 2 * len(latencies), colors="slategrey", linestyles=(0, (1,1)))
        plt.text(0, 2000+height_shift, 2000, ha='center', va='top',
                 fontsize=18, color="slategrey")

    plt.savefig("visual/latencies-{}.jpg".format(app_id))


if __name__ == '__main__':
    if not os.path.exists("./visual"):
        os.mkdir("./visual")
    main(int(sys.argv[1]), int(sys.argv[2]))
