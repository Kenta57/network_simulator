/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

// Network topology
//
//       n0 ----------- n1
//            500 Kbps
//             5 ms
//
// - Flow from n0 to n1 using BulkSendApplication.
// - Tracing of queues and packet receptions to file "tcp-bulk-send.tr"
//   and pcap tracing available when tracing is turned on.

#include <string>
#include <fstream>
#include "ns3/core-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"
#include "ns3/network-module.h"
#include "ns3/packet-sink.h"

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/error-model.h"
#include "ns3/tcp-header.h"
#include "ns3/udp-header.h"
#include "ns3/enum.h"
#include "ns3/event-id.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/traffic-control-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("TcpBulkSendExample");
bool firstCwnd = true;
bool firstSshThr = true;
bool firstRtt = true;
bool firstRto = true;
Ptr<OutputStreamWrapper> cWndStream;
Ptr<OutputStreamWrapper> ssThreshStream;
Ptr<OutputStreamWrapper> rttStream;
Ptr<OutputStreamWrapper> rtoStream;
Ptr<OutputStreamWrapper> nextTxStream;
Ptr<OutputStreamWrapper> nextRxStream;
Ptr<OutputStreamWrapper> inFlightStream;
Ptr<OutputStreamWrapper> ackStream;
Ptr<OutputStreamWrapper> congStateStream;
uint32_t cWndValue;
uint32_t ssThreshValue;
double TH_INTERVAL = 1.0;

// トレース用コールバック関数の設定 関数の引数は決まっている
static void
CwndTracer (Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
{
  // 観測初め　streamに情報を追加していく
  if (firstCwnd)
    {
      *stream->GetStream () << "0.0 " << oldval << std::endl;
      firstCwnd = false;
    }
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval << std::endl;
}

// static void
// SsThreshTracer (Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
// {
//   if (firstSshThr)
//     {
//       *stream->GetStream () << "0.0 " << oldval << std::endl;
//       firstSshThr = false;
//     }
//   *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval << std::endl;
// }

static void
RttTracer (Ptr<OutputStreamWrapper> stream, Time oldval, Time newval)
{
  if (firstRtt)
    {
      *stream->GetStream () << "0.0 " << oldval.GetSeconds () << std::endl;
      firstRtt = false;
    }
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval.GetSeconds () << std::endl;
}

// static void
// RtoTracer (Ptr<OutputStreamWrapper> stream, Time oldval, Time newval)
// {
//   if (firstRto)
//     {
//       *stream->GetStream () << "0.0 " << oldval.GetSeconds () << std::endl;
//       firstRto = false;
//     }
//   *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval.GetSeconds () << std::endl;
// }

// static void
// NextTxTracer (Ptr<OutputStreamWrapper> stream, SequenceNumber32 old, SequenceNumber32 nextTx)
// {
//   *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << nextTx << std::endl;
// }

// static void
// InFlightTracer (Ptr<OutputStreamWrapper> stream, uint32_t old, uint32_t inFlight)
// {
//   *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << inFlight << std::endl;
// }

// static void
// NextRxTracer (Ptr<OutputStreamWrapper> stream, SequenceNumber32 old, SequenceNumber32 nextRx)
// {
//   *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << nextRx << std::endl;
// }

// static void
// AckTracer (Ptr<OutputStreamWrapper> stream, SequenceNumber32 old, SequenceNumber32 newAck)
// {
//   *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newAck << std::endl;
// }

// static void
// CongStateTracer (Ptr<OutputStreamWrapper> stream, TcpSocketState::TcpCongState_t old, TcpSocketState::TcpCongState_t newState)
// {
//   *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newState << std::endl;
// }

// コールバック関数をトレース対象と紐付ける関数
static void
TraceCwnd (uint32_t nodeId, std::string cwnd_tr_file_name)
{
  // asciiトレースファイルに書き込んでくれるhelper関数
  AsciiTraceHelper ascii;
  // cWndStreamはあらかじめ定義しておく(Ptr<OutputStreamWrapper>)
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (cwnd_tr_file_name.c_str ());
  // CongestionWindowの場所(configパス) "/NodeList/[i]/$ns3::TcpL4Protocol/SocketList/[j]" iがノード番号, jがネットワークデバイス番号
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&CwndTracer, stream));
}

// static void
// TraceSsThresh (uint32_t nodeId, std::string ssthresh_tr_file_name)
// {
//   AsciiTraceHelper ascii;
//   Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (ssthresh_tr_file_name.c_str ());
//   std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/SlowStartThreshold";
//   Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&SsThreshTracer, stream));
// }

static void
TraceRtt (uint32_t nodeId, std::string rtt_tr_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (rtt_tr_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/RTT";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&RttTracer, stream));
}

// static void
// TraceRto (uint32_t nodeId, std::string rto_tr_file_name)
// {
//   AsciiTraceHelper ascii;
//   Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (rto_tr_file_name.c_str ());
//   std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/RTO";
//   Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&RtoTracer, stream));
// }

// static void
// TraceNextTx (uint32_t nodeId, std::string &next_tx_seq_file_name)
// {
//   AsciiTraceHelper ascii;
//   Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (next_tx_seq_file_name.c_str ());
//   std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/NextTxSequence";
//   Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&NextTxTracer, stream));
// }

// static void
// TraceInFlight (uint32_t nodeId, std::string &in_flight_file_name)
// {
//   AsciiTraceHelper ascii;
//   Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (in_flight_file_name.c_str ());
//   std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/BytesInFlight";
//   Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&InFlightTracer, stream));
// }

// static void
// TraceNextRx (uint32_t nodeId, std::string &next_rx_seq_file_name)
// {
//   AsciiTraceHelper ascii;
//   Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (next_rx_seq_file_name.c_str ());
//   std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/1/RxBuffer/NextRxSequence";
//   Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&NextRxTracer, stream));
// }

// static void
// TraceAck (uint32_t nodeId, std::string &ack_file_name)
// {
//   AsciiTraceHelper ascii;
//   Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (ack_file_name.c_str ());
//   std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/HighestRxAck";
//   Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&AckTracer, stream));
// }

// static void
// TraceCongState (uint32_t nodeId, std::string &cong_state_file_name)
// {
//   AsciiTraceHelper ascii;
//   Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (cong_state_file_name.c_str ());
//   std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/CongState";
//   Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&CongStateTracer, stream));
// }

static std::string
GetTcpAlgorithm (std::string transport_prot)
{
	std::string alg;
	if (transport_prot.compare ("TcpNewReno") == 0) {
		alg = "ns3::TcpNewReno";
	} else if (transport_prot.compare ("TcpHybla") == 0) {
		alg = "ns3::TcpHybla";
	} else if (transport_prot.compare ("TcpHighSpeed") == 0) {
		alg = "ns3::TcpHighSpeed";
	} else if (transport_prot.compare ("TcpVegas") == 0) {
		alg = "ns3::TcpVegas";
	} else if (transport_prot.compare ("TcpScalable") == 0) {
		alg = "ns3::TcpScalable";
	} else if (transport_prot.compare ("TcpHtcp") == 0) {
		alg = "ns3::TcpHtcp";
	} else if (transport_prot.compare ("TcpVeno") == 0) {
		alg = "ns3::TcpVeno";
	} else if (transport_prot.compare ("TcpBic") == 0) {
		alg = "ns3::TcpBic";
	} else if (transport_prot.compare ("TcpCubic") == 0) {
		alg = "ns3::TcpCubic";
	} else if (transport_prot.compare ("TcpBbr") == 0) {
		alg = "ns3::TcpBbr";
	} else {
		NS_LOG_DEBUG ("Invalid TCP version");
		exit (1);
	}
	return alg;
}

static void
SetTcpAlgorithm2Node (uint32_t nodeId, std::string transport_prot)
{
  // configパス ns3のcoreファイルに書かれている情報の場所を表す？ 今回の場合だとsocketのタイプが格納してある場所
	std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketType";
  // 名前からtype idを呼ぶ
	TypeId tid = TypeId::LookupByName(GetTcpAlgorithm(transport_prot));
  // デフォルトではcubicになっているのでそれをtransport_protに変更
	Config::Set(nodelist, TypeIdValue(tid));
}

// static void // trace throughput in Mbps
// TraceThroughput (Ptr<Application> app, Ptr<OutputStreamWrapper> stream, uint32_t oldTotalBytes)
// {
//   // PacketSinkにcast
// 	Ptr <PacketSink> pktSink = DynamicCast <PacketSink> (app);
//   // sink appが今まで受け取ったtotalのbyte数
// 	uint32_t newTotalBytes = pktSink->GetTotalRx ();
//   // byte -> Mbit 
// 	*stream->GetStream() << Simulator::Now ().GetSeconds () << "\t" << (newTotalBytes - oldTotalBytes)*8.0/TH_INTERVAL/1000/1000 << std::endl;
//   // totalを再帰的に渡すことで差分を取ることできる
// 	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceThroughput, app, stream, newTotalBytes);
// }

// static void
// StartAppTrace(ApplicationContainer sinkapp, std::string th_file_name)
// {
//   // asciiトレースファイルに書き込んでくれるhelper関数
// 	AsciiTraceHelper ascii;
// 	Ptr<OutputStreamWrapper> st1 = ascii.CreateFileStream(th_file_name);
//   // TraceThroughput関数の最初の呼び出し oldTotalBytesを0にしておく
// 	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceThroughput, sinkapp.Get(0), st1, 0);
// }

// static void
// TraceQueue (Ptr< Queue< Packet > > queue, Ptr<OutputStreamWrapper> stream, std::string type)
// {
//   // queueにある*数
// 	uint32_t sizeB = queue->GetNBytes ();
// 	uint32_t sizeP = queue->GetNPackets ();
//   // 受信した*数
// 	uint32_t  recB = queue->GetTotalReceivedBytes ();
// 	uint32_t  recP = queue->GetTotalReceivedPackets ();
//   // dropした*数
// 	uint32_t dropB = queue->GetTotalDroppedBytes ();
// 	uint32_t dropP = queue->GetTotalDroppedPackets ();

//   // typeに応じて単位をbyteかpacketにしたものを書き込む
// 	if(type.compare("bytes") == 0) {
// 		*stream->GetStream() << Simulator::Now ().GetSeconds () << "\t" << sizeB << "\t" << recB << "\t" << dropB << std::endl;
// 	} else {
// 		*stream->GetStream() << Simulator::Now ().GetSeconds () << "\t" << sizeP << "\t" << recP << "\t" << dropP << std::endl;
// 	}
//   // 再帰的に呼び出す
// 	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceQueue, queue, stream, type);
// }

// static void
// StartQueueTrace (Ptr<NetDevice> dev, std::string type, std::string q_file_name)
// {
//   // cast
// 	Ptr<PointToPointNetDevice> nd = StaticCast<PointToPointNetDevice> (dev);
//   // netdeviceのqueueを取り出す
// 	Ptr< Queue< Packet > > queue = nd->GetQueue ();

//   // asciiデータのためのhelper関数
// 	AsciiTraceHelper ascii;
// 	Ptr<OutputStreamWrapper> st1 = ascii.CreateFileStream(q_file_name);

// 	*st1->GetStream() << "Time\t" << "size\t" << "received\t" << "dropped" << "\n";
// 	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceQueue, queue, st1, type);
// }

// static PointToPointHelper
// GetP2PLink (std::string bandwidth, std::string delay, uint32_t q_size)
// {
// 	PointToPointHelper p2p;
// 	p2p.SetDeviceAttribute ("DataRate", StringValue (bandwidth));
// 	p2p.SetChannelAttribute ("Delay", StringValue (delay));
// 	// p2p.SetQueue ("ns3::DropTailQueue", "MaxPackets", UintegerValue (q_size));
// 	p2p.SetQueue ("ns3::DropTailQueue", "MaxSize", StringValue (std::to_string(q_size)+'p'));
// 	return p2p;
// }

int
main (int argc, char *argv[])
{

  bool tracing = false;
  uint32_t maxBytes = 0;
  std::string prefix_file_name = "TcpDelayBase";
  std::string transport_prot = "TcpNewReno";

//
// Allow the user to override any of the defaults at
// run-time, via command-line arguments
//
  CommandLine cmd;
  cmd.AddValue ("tracing", "Flag to enable/disable tracing", tracing);
  cmd.AddValue ("maxBytes",
                "Total number of bytes for application to send", maxBytes);
  cmd.AddValue ("prefix_name", "Prefix of output trace file", prefix_file_name);
  cmd.Parse (argc, argv);

//
// Explicitly create the nodes required by the topology (shown above).
//
  NS_LOG_INFO ("Create nodes.");
  NodeContainer nodes;
  nodes.Create (2);

  NS_LOG_INFO ("Create channels.");

//
// Explicitly create the point-to-point link required by the topology (shown above).
//
  PointToPointHelper pointToPoint;
  pointToPoint.SetDeviceAttribute ("DataRate", StringValue ("10Mbps"));
  pointToPoint.SetChannelAttribute ("Delay", StringValue ("5ms"));

  NetDeviceContainer devices;
  devices = pointToPoint.Install (nodes);

//
// Install the internet stack on the nodes
//
  InternetStackHelper internet;
  internet.Install (nodes);

//
// We've got the "hardware" in place.  Now we need to add IP addresses.
//
  NS_LOG_INFO ("Assign IP Addresses.");
  Ipv4AddressHelper ipv4;
  ipv4.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer i = ipv4.Assign (devices);

  NS_LOG_INFO ("Create Applications.");

//
// Create a BulkSendApplication and install it on node 0
//
  uint16_t port = 9;  // well-known echo port number


  BulkSendHelper source ("ns3::TcpSocketFactory",
                         InetSocketAddress (i.GetAddress (1), port));
  // Set the amount of data to send in bytes.  Zero is unlimited.
  source.SetAttribute ("MaxBytes", UintegerValue (maxBytes));
  ApplicationContainer sourceApps = source.Install (nodes.Get (0));
  sourceApps.Start (Seconds (0.0));
  sourceApps.Stop (Seconds (10.0));

//
// Create a PacketSinkApplication and install it on node 1
//
  PacketSinkHelper sink ("ns3::TcpSocketFactory",
                         InetSocketAddress (Ipv4Address::GetAny (), port));
  ApplicationContainer sinkApps = sink.Install (nodes.Get (1));
  sinkApps.Start (Seconds (0.0));
  sinkApps.Stop (Seconds (40.0));


  SetTcpAlgorithm2Node (nodes.Get (0)->GetId(), transport_prot);
//
// Set up tracing if enabled
//
  if (tracing)
    {
      AsciiTraceHelper ascii;
      pointToPoint.EnableAsciiAll (ascii.CreateFileStream ("tcp-bulk-send.tr"));
      pointToPoint.EnablePcapAll ("tcp-bulk-send", false);
    }

//
// Now, do the actual simulation.
//
  Simulator::Schedule (Seconds (0.00001), &TraceRtt, nodes.Get (0)->GetId(), "data/bulk_send_test-flw-rtt.data");
  Simulator::Schedule (Seconds (0.00001), &TraceCwnd, nodes.Get (0)->GetId(), "data/bulk_send_tes-flw-cwnd.data");


  NS_LOG_INFO ("Run Simulation.");
  Simulator::Stop (Seconds (40.0));
  Simulator::Run ();
  Simulator::Destroy ();
  NS_LOG_INFO ("Done.");

  Ptr<PacketSink> sink1 = DynamicCast<PacketSink> (sinkApps.Get (0));
  std::cout << "Total Bytes Received: " << sink1->GetTotalRx () << std::endl;
}
