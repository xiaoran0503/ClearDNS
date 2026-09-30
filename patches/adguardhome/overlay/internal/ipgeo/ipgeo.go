// Package ipgeo looks up DNS response IPs against an offline ip2region xdb.
// Lookups happen at query-log API display time; nothing is persisted.
package ipgeo

import (
	"log"
	"net"
	"os"
	"strings"
	"sync"

	"github.com/AdguardTeam/AdGuardHome/internal/ipgeo/xdb"
)

const (
	defaultV4Path = "/usr/share/ip2region/ip2region_v4.xdb"
	defaultV6Path = "/usr/share/ip2region/ip2region_v6.xdb"
)

var (
	v4Searcher *xdb.Searcher
	v6Searcher *xdb.Searcher
	cache      sync.Map // string -> string
	cgnat      = net.IPNet{IP: net.IPv4(100, 64, 0, 0), Mask: net.CIDRMask(10, 32)}
)

func init() {
	v4 := os.Getenv("IP2REGION_V4")
	if v4 == "" {
		v4 = defaultV4Path
	}
	v6 := os.Getenv("IP2REGION_V6")
	if v6 == "" {
		v6 = defaultV6Path
	}
	v4Searcher = loadOne(v4, xdb.IPv4)
	v6Searcher = loadOne(v6, xdb.IPv6)
}

func loadOne(path string, ver *xdb.Version) *xdb.Searcher {
	buf, err := xdb.LoadContentFromFile(path)
	if err != nil {
		log.Printf("ipgeo: skip %s: %v", path, err)
		return nil
	}
	s, err := xdb.NewWithBuffer(ver, buf)
	if err != nil {
		log.Printf("ipgeo: searcher %s: %v", path, err)
		return nil
	}
	log.Printf("ipgeo: loaded %s (%d bytes)", path, len(buf))
	return s
}

// Lookup returns a compact geo label for a public A/AAAA value, or "".
func Lookup(ipStr string) string {
	ipStr = strings.TrimSpace(ipStr)
	if ipStr == "" {
		return ""
	}
	if v, ok := cache.Load(ipStr); ok {
		return v.(string)
	}
	geo := lookupUncached(ipStr)
	cache.Store(ipStr, geo)
	return geo
}

func lookupUncached(ipStr string) string {
	ip := net.ParseIP(ipStr)
	if ip == nil || skipIP(ip) {
		return ""
	}
	region, err := search(ip)
	if err != nil || region == "" {
		return ""
	}
	return formatRegion(region)
}

func search(ip net.IP) (string, error) {
	if ip4 := ip.To4(); ip4 != nil {
		if v4Searcher == nil {
			return "", nil
		}
		return v4Searcher.Search(ip4.String())
	}
	if v6Searcher == nil {
		return "", nil
	}
	return v6Searcher.Search(ip.String())
}

func skipIP(ip net.IP) bool {
	if ip.IsLoopback() || ip.IsPrivate() || ip.IsUnspecified() ||
		ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() || ip.IsMulticast() {
		return true
	}
	if ip4 := ip.To4(); ip4 != nil && cgnat.Contains(ip4) {
		return true
	}
	return false
}
