package ipgeo

import "strings"

// formatRegion turns ip2region "Country|Province|City|ISP|CC" into a short UI label.
func formatRegion(region string) string {
	parts := strings.Split(region, "|")
	for len(parts) < 5 {
		parts = append(parts, "")
	}
	country := nz(parts[0])
	province := nz(parts[1])
	city := nz(parts[2])
	isp := nz(parts[3])
	cc := nz(parts[4])
	if country == "" && province == "" && city == "" && isp == "" {
		return ""
	}
	if isPrivateLabel(country) || isPrivateLabel(province) {
		return ""
	}
	if isCN(country, cc) {
		loc := stripCN(city)
		if loc == "" {
			loc = stripCN(province)
		}
		if loc == "" {
			loc = "中国"
		}
		return joinNonEmpty(" ", loc, isp)
	}
	return joinNonEmpty(" ", mapCountry(country, cc), isp)
}

func nz(s string) string {
	s = strings.TrimSpace(s)
	if s == "" || s == "0" || s == "*" {
		return ""
	}
	return s
}

func stripCN(s string) string {
	s = nz(s)
	s = strings.TrimSuffix(s, "省")
	s = strings.TrimSuffix(s, "市")
	return s
}

func isCN(country, cc string) bool {
	return strings.EqualFold(cc, "CN") || country == "中国" || strings.EqualFold(country, "China")
}

func isPrivateLabel(s string) bool {
	return strings.Contains(s, "内网") || s == "保留地址" || s == "本机地址" || s == "局域网" ||
		strings.EqualFold(s, "Private") || strings.EqualFold(s, "Reserved")
}

func joinNonEmpty(sep string, parts ...string) string {
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if p != "" {
			out = append(out, p)
		}
	}
	return strings.Join(out, sep)
}

func mapCountry(country, cc string) string {
	if v, ok := countryNames[strings.ToUpper(cc)]; ok {
		return v
	}
	if v, ok := countryNames[strings.ToLower(country)]; ok {
		return v
	}
	if v, ok := countryNames[country]; ok {
		return v
	}
	if country != "" {
		return country
	}
	return cc
}

// Keys: ISO cc (upper), English names (lower), and a few native names.
var countryNames = map[string]string{
	"CN": "中国", "china": "中国", "中国": "中国",
	"US": "美国", "united states": "美国", "usa": "美国", "united states of america": "美国",
	"JP": "日本", "japan": "日本",
	"SG": "新加坡", "singapore": "新加坡",
	"HK": "香港", "hong kong": "香港",
	"TW": "台湾", "taiwan": "台湾",
	"MO": "澳门", "macao": "澳门", "macau": "澳门",
	"KR": "韩国", "south korea": "韩国", "korea": "韩国", "republic of korea": "韩国",
	"DE": "德国", "germany": "德国",
	"NL": "荷兰", "netherlands": "荷兰",
	"GB": "英国", "UK": "英国", "united kingdom": "英国", "great britain": "英国",
	"RU": "俄罗斯", "russia": "俄罗斯",
	"AU": "澳大利亚", "australia": "澳大利亚",
	"FR": "法国", "france": "法国",
	"CA": "加拿大", "canada": "加拿大",
	"IN": "印度", "india": "印度",
	"BR": "巴西", "brazil": "巴西",
	"IE": "爱尔兰", "ireland": "爱尔兰",
	"SE": "瑞典", "sweden": "瑞典",
	"FI": "芬兰", "finland": "芬兰",
	"IT": "意大利", "italy": "意大利",
	"ES": "西班牙", "spain": "西班牙",
	"CH": "瑞士", "switzerland": "瑞士",
	"TH": "泰国", "thailand": "泰国",
	"VN": "越南", "vietnam": "越南", "viet nam": "越南",
	"MY": "马来西亚", "malaysia": "马来西亚",
	"ID": "印度尼西亚", "indonesia": "印度尼西亚",
	"PH": "菲律宾", "philippines": "菲律宾",
	"TR": "土耳其", "turkey": "土耳其",
	"PL": "波兰", "poland": "波兰",
	"UA": "乌克兰", "ukraine": "乌克兰",
	"ZA": "南非", "south africa": "南非",
	"MX": "墨西哥", "mexico": "墨西哥",
	"AR": "阿根廷", "argentina": "阿根廷",
	"NZ": "新西兰", "new zealand": "新西兰",
	"AE": "阿联酋", "united arab emirates": "阿联酋",
	"SA": "沙特阿拉伯", "saudi arabia": "沙特阿拉伯",
	"IL": "以色列", "israel": "以色列",
}
