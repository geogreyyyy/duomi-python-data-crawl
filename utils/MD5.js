window = global;

;;(function() {
    "use strict";
    var a, t, e, i, s, r = {
        96706: function(e, t, n) {
            var r, i, o, a, s;
            r = n(1048),
            i = n(6636).utf8,
            o = n(13149),
            a = n(6636).bin,
            s = function(e, t) {
                e.constructor == String ? e = t && "binary" === t.encoding ? a.stringToBytes(e) : i.stringToBytes(e) : o(e) ? e = Array.prototype.slice.call(e, 0) : Array.isArray(e) || e.constructor === Uint8Array || (e = e.toString());
                for (var n = r.bytesToWords(e), c = 8 * e.length, u = 1732584193, l = -271733879, d = -1732584194, f = 271733878, p = 0; p < n.length; p++)
                    n[p] = 16711935 & (n[p] << 8 | n[p] >>> 24) | 4278255360 & (n[p] << 24 | n[p] >>> 8);
                n[c >>> 5] |= 128 << c % 32,
                n[14 + (c + 64 >>> 9 << 4)] = c;
                var h = s._ff
                  , v = s._gg
                  , m = s._hh
                  , g = s._ii;
                for (p = 0; p < n.length; p += 16) {
                    var y = u
                      , _ = l
                      , b = d
                      , w = f;
                    u = h(u, l, d, f, n[p + 0], 7, -680876936),
                    f = h(f, u, l, d, n[p + 1], 12, -389564586),
                    d = h(d, f, u, l, n[p + 2], 17, 606105819),
                    l = h(l, d, f, u, n[p + 3], 22, -1044525330),
                    u = h(u, l, d, f, n[p + 4], 7, -176418897),
                    f = h(f, u, l, d, n[p + 5], 12, 1200080426),
                    d = h(d, f, u, l, n[p + 6], 17, -1473231341),
                    l = h(l, d, f, u, n[p + 7], 22, -45705983),
                    u = h(u, l, d, f, n[p + 8], 7, 1770035416),
                    f = h(f, u, l, d, n[p + 9], 12, -1958414417),
                    d = h(d, f, u, l, n[p + 10], 17, -42063),
                    l = h(l, d, f, u, n[p + 11], 22, -1990404162),
                    u = h(u, l, d, f, n[p + 12], 7, 1804603682),
                    f = h(f, u, l, d, n[p + 13], 12, -40341101),
                    d = h(d, f, u, l, n[p + 14], 17, -1502002290),
                    l = h(l, d, f, u, n[p + 15], 22, 1236535329),
                    u = v(u, l, d, f, n[p + 1], 5, -165796510),
                    f = v(f, u, l, d, n[p + 6], 9, -1069501632),
                    d = v(d, f, u, l, n[p + 11], 14, 643717713),
                    l = v(l, d, f, u, n[p + 0], 20, -373897302),
                    u = v(u, l, d, f, n[p + 5], 5, -701558691),
                    f = v(f, u, l, d, n[p + 10], 9, 38016083),
                    d = v(d, f, u, l, n[p + 15], 14, -660478335),
                    l = v(l, d, f, u, n[p + 4], 20, -405537848),
                    u = v(u, l, d, f, n[p + 9], 5, 568446438),
                    f = v(f, u, l, d, n[p + 14], 9, -1019803690),
                    d = v(d, f, u, l, n[p + 3], 14, -187363961),
                    l = v(l, d, f, u, n[p + 8], 20, 1163531501),
                    u = v(u, l, d, f, n[p + 13], 5, -1444681467),
                    f = v(f, u, l, d, n[p + 2], 9, -51403784),
                    d = v(d, f, u, l, n[p + 7], 14, 1735328473),
                    l = v(l, d, f, u, n[p + 12], 20, -1926607734),
                    u = m(u, l, d, f, n[p + 5], 4, -378558),
                    f = m(f, u, l, d, n[p + 8], 11, -2022574463),
                    d = m(d, f, u, l, n[p + 11], 16, 1839030562),
                    l = m(l, d, f, u, n[p + 14], 23, -35309556),
                    u = m(u, l, d, f, n[p + 1], 4, -1530992060),
                    f = m(f, u, l, d, n[p + 4], 11, 1272893353),
                    d = m(d, f, u, l, n[p + 7], 16, -155497632),
                    l = m(l, d, f, u, n[p + 10], 23, -1094730640),
                    u = m(u, l, d, f, n[p + 13], 4, 681279174),
                    f = m(f, u, l, d, n[p + 0], 11, -358537222),
                    d = m(d, f, u, l, n[p + 3], 16, -722521979),
                    l = m(l, d, f, u, n[p + 6], 23, 76029189),
                    u = m(u, l, d, f, n[p + 9], 4, -640364487),
                    f = m(f, u, l, d, n[p + 12], 11, -421815835),
                    d = m(d, f, u, l, n[p + 15], 16, 530742520),
                    l = m(l, d, f, u, n[p + 2], 23, -995338651),
                    u = g(u, l, d, f, n[p + 0], 6, -198630844),
                    f = g(f, u, l, d, n[p + 7], 10, 1126891415),
                    d = g(d, f, u, l, n[p + 14], 15, -1416354905),
                    l = g(l, d, f, u, n[p + 5], 21, -57434055),
                    u = g(u, l, d, f, n[p + 12], 6, 1700485571),
                    f = g(f, u, l, d, n[p + 3], 10, -1894986606),
                    d = g(d, f, u, l, n[p + 10], 15, -1051523),
                    l = g(l, d, f, u, n[p + 1], 21, -2054922799),
                    u = g(u, l, d, f, n[p + 8], 6, 1873313359),
                    f = g(f, u, l, d, n[p + 15], 10, -30611744),
                    d = g(d, f, u, l, n[p + 6], 15, -1560198380),
                    l = g(l, d, f, u, n[p + 13], 21, 1309151649),
                    u = g(u, l, d, f, n[p + 4], 6, -145523070),
                    f = g(f, u, l, d, n[p + 11], 10, -1120210379),
                    d = g(d, f, u, l, n[p + 2], 15, 718787259),
                    l = g(l, d, f, u, n[p + 9], 21, -343485551),
                    u = u + y >>> 0,
                    l = l + _ >>> 0,
                    d = d + b >>> 0,
                    f = f + w >>> 0
                }
                return r.endian([u, l, d, f])
            }
            ,
            s._ff = function(e, t, n, r, i, o, a) {
                var s = e + (t & n | ~t & r) + (i >>> 0) + a;
                return (s << o | s >>> 32 - o) + t
            }
            ,
            s._gg = function(e, t, n, r, i, o, a) {
                var s = e + (t & r | n & ~r) + (i >>> 0) + a;
                return (s << o | s >>> 32 - o) + t
            }
            ,
            s._hh = function(e, t, n, r, i, o, a) {
                var s = e + (t ^ n ^ r) + (i >>> 0) + a;
                return (s << o | s >>> 32 - o) + t
            }
            ,
            s._ii = function(e, t, n, r, i, o, a) {
                var s = e + (n ^ (t | ~r)) + (i >>> 0) + a;
                return (s << o | s >>> 32 - o) + t
            }
            ,
            s._blocksize = 16,
            s._digestsize = 16,
            e.exports = function(e, t) {
                if (null == e)
                    throw new Error("Illegal argument " + e);
                var n = r.wordsToBytes(s(e, t));
                return t && t.asBytes ? n : t && t.asString ? a.bytesToString(n) : r.bytesToHex(n)
            }
        },
        1048: function(e) {
            var t, n;
            t = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
            n = {
                rotl: function(e, t) {
                    return e << t | e >>> 32 - t
                },
                rotr: function(e, t) {
                    return e << 32 - t | e >>> t
                },
                endian: function(e) {
                    if (e.constructor == Number)
                        return 16711935 & n.rotl(e, 8) | 4278255360 & n.rotl(e, 24);
                    for (var t = 0; t < e.length; t++)
                        e[t] = n.endian(e[t]);
                    return e
                },
                randomBytes: function(e) {
                    for (var t = []; e > 0; e--)
                        t.push(Math.floor(256 * Math.random()));
                    return t
                },
                bytesToWords: function(e) {
                    for (var t = [], n = 0, r = 0; n < e.length; n++,
                    r += 8)
                        t[r >>> 5] |= e[n] << 24 - r % 32;
                    return t
                },
                wordsToBytes: function(e) {
                    for (var t = [], n = 0; n < 32 * e.length; n += 8)
                        t.push(e[n >>> 5] >>> 24 - n % 32 & 255);
                    return t
                },
                bytesToHex: function(e) {
                    for (var t = [], n = 0; n < e.length; n++)
                        t.push((e[n] >>> 4).toString(16)),
                        t.push((15 & e[n]).toString(16));
                    return t.join("")
                },
                hexToBytes: function(e) {
                    for (var t = [], n = 0; n < e.length; n += 2)
                        t.push(parseInt(e.substr(n, 2), 16));
                    return t
                },
                bytesToBase64: function(e) {
                    for (var n = [], r = 0; r < e.length; r += 3)
                        for (var i = e[r] << 16 | e[r + 1] << 8 | e[r + 2], o = 0; o < 4; o++)
                            8 * r + 6 * o <= 8 * e.length ? n.push(t.charAt(i >>> 6 * (3 - o) & 63)) : n.push("=");
                    return n.join("")
                },
                base64ToBytes: function(e) {
                    e = e.replace(/[^A-Z0-9+\/]/gi, "");
                    for (var n = [], r = 0, i = 0; r < e.length; i = ++r % 4)
                        0 != i && n.push((t.indexOf(e.charAt(r - 1)) & Math.pow(2, -2 * i + 8) - 1) << 2 * i | t.indexOf(e.charAt(r)) >>> 6 - 2 * i);
                    return n
                }
            },
            e.exports = n
        },
        6636: function(e) {
            var t = {
                utf8: {
                    stringToBytes: function(e) {
                        return t.bin.stringToBytes(unescape(encodeURIComponent(e)))
                    },
                    bytesToString: function(e) {
                        return decodeURIComponent(escape(t.bin.bytesToString(e)))
                    }
                },
                bin: {
                    stringToBytes: function(e) {
                        for (var t = [], n = 0; n < e.length; n++)
                            t.push(255 & e.charCodeAt(n));
                        return t
                    },
                    bytesToString: function(e) {
                        for (var t = [], n = 0; n < e.length; n++)
                            t.push(String.fromCharCode(e[n]));
                        return t.join("")
                    }
                }
            };
            e.exports = t
        },
        
        13149: function(e) {
            function t(e) {
                return !!e.constructor && "function" == typeof e.constructor.isBuffer && e.constructor.isBuffer(e)
            }
            function n(e) {
                return "function" == typeof e.readFloatLE && "function" == typeof e.slice && t(e.slice(0, 0))
            }
            e.exports = function(e) {
                return null != e && (t(e) || n(e) || !!e._isBuffer)
            }
        },
    }, n = {};
    function o(a) {
        var t = n[a];
        if (void 0 !== t)
            return t.exports;
        var e = n[a] = {
            id: a,
            loaded: !1,
            exports: {}
        };
        return r[a].call(e.exports, e, e.exports, o),
        e.loaded = !0,
        e.exports
    }
    o.m = r,
    o.amdO = {},
    a = [],
    o.O = function(t, e, i, s) {
        if (!e) {
            var r = 1 / 0;
            for (d = 0; d < a.length; d++) {
                e = a[d][0],
                i = a[d][1],
                s = a[d][2];
                for (var n = !0, l = 0; l < e.length; l++)
                    (!1 & s || r >= s) && Object.keys(o.O).every((function(a) {
                        return o.O[a](e[l])
                    }
                    )) ? e.splice(l--, 1) : (n = !1,
                    s < r && (r = s));
                if (n) {
                    a.splice(d--, 1);
                    var c = i();
                    void 0 !== c && (t = c)
                }
            }
            return t
        }
        s = s || 0;
        for (var d = a.length; d > 0 && a[d - 1][2] > s; d--)
            a[d] = a[d - 1];
        a[d] = [e, i, s]
    }
    ,
    o.n = function(a) {
        var t = a && a.__esModule ? function() {
            return a["default"]
        }
        : function() {
            return a
        }
        ;
        return o.d(t, {
            a: t
        }),
        t
    }
    ,
    e = Object.getPrototypeOf ? function(a) {
        return Object.getPrototypeOf(a)
    }
    : function(a) {
        return a.__proto__
    }
    ,
    o.t = function(a, i) {
        if (1 & i && (a = this(a)),
        8 & i)
            return a;
        if ("object" == typeof a && a) {
            if (4 & i && a.__esModule)
                return a;
            if (16 & i && "function" == typeof a.then)
                return a
        }
        var s = Object.create(null);
        o.r(s);
        var r = {};
        t = t || [null, e({}), e([]), e(e)];
        for (var n = 2 & i && a; "object" == typeof n && !~t.indexOf(n); n = e(n))
            Object.getOwnPropertyNames(n).forEach((function(t) {
                r[t] = function() {
                    return a[t]
                }
            }
            ));
        return r["default"] = function() {
            return a
        }
        ,
        o.d(s, r),
        s
    }
    ,
    o.d = function(a, t) {
        for (var e in t)
            o.o(t, e) && !o.o(a, e) && Object.defineProperty(a, e, {
                enumerable: !0,
                get: t[e]
            })
    }
    ,
    o.f = {},
    o.e = function(a) {
        return Promise.all(Object.keys(o.f).reduce((function(t, e) {
            return o.f[e](a, t),
            t
        }
        ), []))
    }
    ,
    o.u = function(a) {
        return "assets/js/" + ({
            1597: "blind-choose-brand-review",
            1676: "message",
            2086: "ad-data-security-verify",
            2598: "ad-add-fund",
            3146: "ad-qualification-form",
            3568: "ad-create-success",
            4832: "ad-send-invitation",
            5136: "ad-dashboard-wrap",
            5240: "talent-data-security",
            5293: "ad-campaign-report-detail",
            5369: "ad-order-v2",
            5799: "ad-notifications",
            5991: "ad-e-shop",
            6326: "ad-content",
            6528: "ad-short-list-creators",
            6600: "ad-campaign-report-list",
            6622: "ad-create-campaign",
            6712: "ad-send-success",
            6858: "ad-short-list-new",
            7434: "ad-success-wrap",
            7523: "ad-financial",
            7605: "content-cooperation-list",
            7720: "ad-payment-callback",
            7753: "ad-short-list-flod",
            7859: "ad-bc-link-request",
            8130: "ad-market",
            9066: "ad-create-starter-pack",
            9289: "ad-content-engine",
            9294: "chunk-echarts",
            9630: "ad-searching-creator-progress",
            9826: "ad-business-center"
        }[a] || a) + "." + {
            430: "540e6a3a",
            942: "3350055d",
            1597: "d3929513",
            1676: "bb5a31f3",
            2086: "26b981f6",
            2129: "a08c4c15",
            2598: "a30be837",
            3046: "505bb4f0",
            3146: "9056a26e",
            3440: "0ea7e5a4",
            3568: "9a7d16c6",
            4832: "5e0aeda7",
            5136: "534c0005",
            5240: "dad1e818",
            5293: "598afe0c",
            5369: "782a2923",
            5707: "6bcbd9b9",
            5799: "0f8a915c",
            5991: "e28bfe3b",
            6010: "d115e4b5",
            6326: "ded4f8d5",
            6345: "1a1da2af",
            6465: "0d2fc3e7",
            6528: "11b5a90b",
            6600: "f7e9fd45",
            6622: "7dcf83fb",
            6712: "8e59a57d",
            6858: "6c797471",
            7298: "84fcc111",
            7434: "646840dd",
            7523: "79112067",
            7605: "a4b7ae91",
            7720: "dbbcf321",
            7753: "206f053a",
            7859: "b23c906b",
            8011: "c3f50e3c",
            8130: "891c940f",
            8279: "951c8032",
            8434: "538e46bf",
            9066: "89fc560b",
            9289: "dff8beaf",
            9294: "9be7c33c",
            9425: "5c055184",
            9630: "9c96fe2a",
            9826: "0967bb4e"
        }[a] + ".js"
    }
    ,
    o.miniCssF = function(a) {
        return "assets/css/" + ({
            1597: "blind-choose-brand-review",
            1676: "message",
            2086: "ad-data-security-verify",
            2598: "ad-add-fund",
            3146: "ad-qualification-form",
            3568: "ad-create-success",
            4832: "ad-send-invitation",
            5136: "ad-dashboard-wrap",
            5240: "talent-data-security",
            5293: "ad-campaign-report-detail",
            5369: "ad-order-v2",
            5799: "ad-notifications",
            5991: "ad-e-shop",
            6326: "ad-content",
            6528: "ad-short-list-creators",
            6600: "ad-campaign-report-list",
            6622: "ad-create-campaign",
            6712: "ad-send-success",
            6858: "ad-short-list-new",
            7523: "ad-financial",
            7605: "content-cooperation-list",
            7720: "ad-payment-callback",
            7753: "ad-short-list-flod",
            7859: "ad-bc-link-request",
            8130: "ad-market",
            9066: "ad-create-starter-pack",
            9289: "ad-content-engine",
            9630: "ad-searching-creator-progress",
            9826: "ad-business-center"
        }[a] || a) + "." + o.h().slice(0, 4) + ".css"
    }
    ,
    o.h = function() {
        return "585124e070840797"
    }
    ,
    o.g = function() {
        if ("object" == typeof globalThis)
            return globalThis;
        try {
            return this || new Function("return this")()
        } catch (a) {
            if ("object" == typeof window)
                return window
        }
    }(),
    o.o = function(a, t) {
        return Object.prototype.hasOwnProperty.call(a, t)
    }
    ,
    i = {},
    s = "star_fe_i18n:",
    o.l = function(a, t, e, r) {
        if (i[a])
            i[a].push(t);
        else {
            var n, l;
            if (void 0 !== e)
                for (var c = document.getElementsByTagName("script"), d = 0; d < c.length; d++) {
                    var p = c[d];
                    if (p.getAttribute("src") == a || p.getAttribute("data-webpack") == s + e) {
                        n = p;
                        break
                    }
                }
            n || (l = !0,
            n = document.createElement("script"),
            n.charset = "utf-8",
            n.timeout = 120,
            o.nc && n.setAttribute("nonce", o.nc),
            n.setAttribute("data-webpack", s + e),
            n.src = a),
            i[a] = [t];
            var m = function(t, e) {
                n.onerror = n.onload = null,
                clearTimeout(x);
                var s = i[a];
                if (delete i[a],
                n.parentNode && n.parentNode.removeChild(n),
                s && s.forEach((function(a) {
                    return a(e)
                }
                )),
                t)
                    return t(e)
            }
              , x = setTimeout(m.bind(null, void 0, {
                type: "timeout",
                target: n
            }), 12e4);
            n.onerror = m.bind(null, n.onerror),
            n.onload = m.bind(null, n.onload),
            l && document.head.appendChild(n)
        }
    }
    ,
    o.r = function(a) {
        "undefined" != typeof Symbol && Symbol.toStringTag && Object.defineProperty(a, Symbol.toStringTag, {
            value: "Module"
        }),
        Object.defineProperty(a, "__esModule", {
            value: !0
        })
    }
    ,
    o.nmd = function(a) {
        return a.paths = [],
        a.children || (a.children = []),
        a
    }
    ,
    o.j = 2321,
    o.p = "//sf-static.tiktokcdn.com/obj/tiktok-creator-market-sg/obj/star_fe_i18n_sg/";

    window.pick = o;
}
)();

var i = pick(96706)
, o = pick.n(i);
const r = "c040a11e10d42f8205a267904f49c5bd";
function n(e) {
    return null == e
}
function c(e) {
    return ["string", "number"].includes(typeof e)
}
function s(e) {
    return Array.isArray(e)
}
function l(e) {
    const t = Object.keys(e).sort().map((t=>{
        const a = e[t];
        return n(a) ? "" : `${t}${c(a) ? a : t}`
    }
    )).join("");
    console.log(t)
    return o()(t + r)
}


var data = {
    "page": 2,
    "limit": 24,
    "sort_type": 2,
    "query": "",
    "sort_field": "comp_rank",
    "use_creator_v2": true,
    "service_name": "search.AdTcmSearchService",
    "service_method": "AuthorPlazaSearch"
}

console.log(l(data))