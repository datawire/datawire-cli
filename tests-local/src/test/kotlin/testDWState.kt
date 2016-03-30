package DWSTester

import java.io.File
import kotlin.test.*
import org.junit.Test as test

import DatawireState.DatawireState

class TestDWState {
	@test fun check() {
		val path: String = System.getProperty("GoldPath")

		println("running check " + path)

		val goldInfo = File(path).readLines()

		var i: Int = 0

		val goldDefaultPath = goldInfo[i++]
		val goldOrgID = goldInfo[i++]
		val goldEmail = goldInfo[i++]

		println("goldDefaultPath " + goldDefaultPath)

		val tokens: MutableMap<String, String> = hashMapOf()
		val services: MutableList<String> = mutableListOf()

		// Yeah, I know, this isn't terribly Kotlinesque. Cope. [ :) ]
		goldInfo.takeLast(goldInfo.size - i).forEach {
			val fields = it.split(":::")

			val svcHandle = fields[0]
			val svcToken = fields[1]

			tokens[svcHandle] = svcToken
			services.add(svcHandle)
		}

        val dwState = DatawireState();

		assertEquals(dwState.defaultStatePath(), goldDefaultPath);

        dwState.loadDefaultState();

		assertEquals(dwState.getCurrentOrgID(), goldOrgID);
		assertEquals(dwState.getCurrentEmail(), goldEmail);

		assertEquals(true, true)
	}
}
