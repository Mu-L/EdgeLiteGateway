#!/usr/bin/env python3
"""浏览 OPC UA 服务器节点结构。"""
from asyncua import Client
import asyncio

async def browse():
    client = Client("opc.tcp://127.0.0.1:4840")
    await client.connect()
    try:
        objects = client.get_objects_node()
        children = await objects.get_children()
        for child in children:
            bname = await child.read_browse_name()
            nid = child.nodeid
            print(f"Object: NodeId={nid} BrowseName={bname}")
            try:
                sub_children = await child.get_children()
                for sub in sub_children:
                    sub_bname = await sub.read_browse_name()
                    sub_nid = sub.nodeid
                    try:
                        val = await sub.read_value()
                    except:
                        val = "N/A"
                    print(f"  Child: NodeId={sub_nid} BrowseName={sub_bname} Value={val}")
            except Exception as e:
                print(f"  (no children: {e})")
    finally:
        await client.disconnect()

asyncio.run(browse())
